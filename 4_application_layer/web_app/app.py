#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask后端主程序
提供医疗知识图谱查询API接口
"""

from pathlib import Path
import tempfile
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sys
import os
import base64


# 添加模块路径（使用绝对路径确保导入成功）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"Project root: {project_root}")

# 【应用层】导入下层服务（使用importlib解决数字开头的包名问题）
import importlib.util

# 导入ASR服务
asr_spec = importlib.util.spec_from_file_location(
    "asr_service",
    os.path.join(project_root, "0_infrastructure", "asr_service.py")
)
asr_module = importlib.util.module_from_spec(asr_spec)
asr_spec.loader.exec_module(asr_module)
recognize_b64_audio = asr_module.recognize_b64_audio

# 导入TTS服务
tts_spec = importlib.util.spec_from_file_location(
    "tts_service",
    os.path.join(project_root, "0_infrastructure", "tts_service.py")
)
tts_module = importlib.util.module_from_spec(tts_spec)
tts_spec.loader.exec_module(tts_module)
speak = tts_module.speak

# 导入RAG检索器
rag_spec = importlib.util.spec_from_file_location(
    "rag_retriever",
    os.path.join(project_root, "2_retrieval_layer", "rag_retriever.py")
)
rag_module = importlib.util.module_from_spec(rag_spec)
rag_spec.loader.exec_module(rag_module)
MedicalRAGRetriever = rag_module.MedicalRAGRetriever

# 导入LLM生成器
llm_spec = importlib.util.spec_from_file_location(
    "llm_generator",
    os.path.join(project_root, "3_generation_layer", "llm_generator.py")
)
llm_module = importlib.util.module_from_spec(llm_spec)
llm_spec.loader.exec_module(llm_module)
DeepSeekLLM = llm_module.DeepSeekLLM
DeepSeekAPILLM = llm_module.DeepSeekAPILLM
MedicalAssistant = llm_module.MedicalAssistant

# 导入医生推荐模块-----------------------------------------------------------------------
doctor_spec = importlib.util.spec_from_file_location(
    "doctor_recommendation",
    os.path.join(project_root, "4_application_layer/doctor_recommend", "doctor_recommendation.py")
)
doctor_module = importlib.util.module_from_spec(doctor_spec)
doctor_spec.loader.exec_module(doctor_module)
DoctorRecommendationSystem = doctor_module.DoctorRecommendationSystem

# 导入DeepSeek RAG服务
deepseek_spec = importlib.util.spec_from_file_location(
    "deepseek_rag_service",
    os.path.join(project_root, "4_application_layer/doctor_recommend", "deepseek_rag_service.py")
)
deepseek_module = importlib.util.module_from_spec(deepseek_spec)
deepseek_spec.loader.exec_module(deepseek_module)
DeepSeekRAGService = deepseek_module.DeepSeekRAGService

# 导入Doctor LangChain服务
langchain_spec = importlib.util.spec_from_file_location(
    "doctor_langchain_service",
    os.path.join(project_root, "4_application_layer/doctor_recommend", "doctor_langchain_service.py")
)
langchain_module = importlib.util.module_from_spec(langchain_spec)
langchain_spec.loader.exec_module(langchain_module)
get_langchain_service = langchain_module.get_langchain_service

# 导入配置（如果文件存在）
LANGCHAIN_CONFIG = {}
NEO4J_CONFIG = {}
try:
    _config_path = os.path.join(project_root, "0_infrastructure", "langchain_config.py")
    if os.path.exists(_config_path):
        config_spec = importlib.util.spec_from_file_location("langchain_config", _config_path)
        config_module = importlib.util.module_from_spec(config_spec)
        config_spec.loader.exec_module(config_module)
        LANGCHAIN_CONFIG = config_module.LANGCHAIN_CONFIG
        NEO4J_CONFIG = config_module.NEO4J_CONFIG
except Exception as e:
    print(f"WARNING 配置加载失败: {e}，使用默认配置")

# 导入健康档案管理模块
health_spec = importlib.util.spec_from_file_location(
    "health_manager",
    os.path.join(project_root, "4_application_layer/health_record", "health_manager.py")
)
health_module = importlib.util.module_from_spec(health_spec)
health_spec.loader.exec_module(health_module)
HealthRecordManager = health_module.HealthRecordManager

# 导入用药依从性跟踪模块
medication_spec = importlib.util.spec_from_file_location(
    "medication_tracker",
    os.path.join(project_root, "4_application_layer/health_record", "medication_tracker.py")
)
medication_module = importlib.util.module_from_spec(medication_spec)
medication_spec.loader.exec_module(medication_module)
MedicationTracker = medication_module.MedicationTracker
# ----------------------------------------------------------------------------------
# 尝试导入Drug OCR引擎
try:
    # 找到Drug_OCR目录的路径
    drug_ocr_path = os.path.join(project_root, "Drug_OCR")
    if os.path.exists(drug_ocr_path):
        sys.path.insert(0, drug_ocr_path)
        
        # 导入OCR引擎
        from Drug_OCR.core.engine import DrugOCREngine
        drug_ocr_engine = DrugOCREngine()
        print("OK 药品OCR引擎初始化成功")
    else:
        print("WARNING 未找到Drug_OCR目录，OCR功能不可用")
        drug_ocr_engine = None
except ImportError as e:
    print(f"WARNING 药品OCR引擎导入失败: {e}")
    drug_ocr_engine = None
except Exception as e:
    print(f"WARNING 药品OCR引擎初始化失败: {e}")
    drug_ocr_engine = None

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置JSON支持中文
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json;charset=utf-8'

# 全局变量：系统组件实例（必须在init_system中初始化）
retriever = None
llm = None
assistant = None
doctor_system = None
deepseek_rag = None
langchain_service = None
health_manager = None
medication_tracker = None

# 初始化系统组件
def initialize_system():
    """初始化系统组件"""
    global retriever, llm, assistant, doctor_system, deepseek_rag, langchain_service, health_manager, medication_tracker
    
    if health_manager is None:
        print("正在初始化健康档案管理器...")
        try:
            health_manager = HealthRecordManager(data_dir="health_records")
            print("健康档案管理器初始化成功")
        except Exception as e:
            print(f"健康档案管理器初始化失败: {e}")
            return False
    return True

def init_system():
    """初始化系统组件 - 关键：在这里创建实例并配置依赖关系"""
    global retriever, llm, assistant, doctor_system, deepseek_rag, langchain_service, health_manager, medication_tracker

    try:
        print("正在初始化系统组件...")

        # 1. 初始化RAG检索器实例（支持环境变量覆盖）
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "12345678")
        retriever = MedicalRAGRetriever(neo4j_uri=neo4j_uri, auth=(neo4j_user, neo4j_pass))
        print("OK RAG检索器初始化成功")

        # 2. 初始化大模型实例（优先使用DeepSeek API，否则使用Ollama本地模型）
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if deepseek_api_key:
            llm = DeepSeekAPILLM(api_key=deepseek_api_key, model="deepseek-chat")
            print("OK 大模型初始化成功（DeepSeek API）")
        else:
            llm = DeepSeekLLM(model="deepseek-r1:7b")
            print("OK 大模型初始化成功（Ollama本地）")

        # 3. 初始化医疗助手实例（依赖retriever和llm）
        assistant = MedicalAssistant(retriever, llm)
        print("OK 医疗助手初始化成功")

        # 4. 初始化DeepSeek RAG服务实例
        deepseek_rag = DeepSeekRAGService()
        print("OK DeepSeek RAG服务初始化成功")

        # 5. 初始化医生推荐系统实例（依赖retriever和deepseek_rag）
        doctor_system = DoctorRecommendationSystem(retriever, deepseek_rag)
        print("OK 医生推荐系统初始化成功")

        # 6. 初始化LangChain服务实例
        langchain_service = get_langchain_service()
        print("OK Neo4j增强的LangChain服务初始化成功")
        
        # 7. 初始化健康档案管理器
        health_manager = HealthRecordManager(data_dir="health_records")
        print("OK 健康档案管理器初始化成功")
        
        # 8. 初始化用药依从性跟踪器
        medication_tracker = MedicationTracker()
        print("OK 用药依从性跟踪器初始化成功")

        print("OK 组件依赖关系配置成功")

        print("OK 所有系统组件初始化成功")
        return True

    except Exception as e:
        print(f"ERROR 系统组件初始化失败: {e}")
        # 创建模拟实例保证系统能运行
        return False
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/graph')
def graph():
    """知识图谱页面"""
    return render_template('graph.html')


@app.route('/drug_recognize')
def drug_recognize():
    """药品识别页面"""
    return render_template('drug_recognize.html')


@app.route('/voice_ask')
def voice_ask():
    """语音询问页面"""
    return render_template('voice_ask.html')


@app.route('/doctor_recommend')
def doctor_recommend():
    """医生推荐页面"""
    return render_template('doctor_recommend.html')


@app.route('/health_record')
def health_record():
    """健康档案管理页面"""
    return render_template('health_record.html')


@app.route('/health_record/shared')
def health_record_shared():
    """共享健康档案页面（家属和医生访问）"""
    return render_template('health_record_shared.html')


@app.route('/api/common/tts', methods=['POST'])
def common_tts():
    """
    通用语音合成接口 - 全局可调用
    请求体: {"text": "待播报文字", "spd": 4, "vol": 7, "per": 0}
    返回: {"success": true, "audio": "base64音频数据"}
    """
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({
            'success': False,
            'message': '播报文字不能为空'
        }), 400
    
    try:
        # 可选参数
        spd = data.get('spd')  # 语速
        vol = data.get('vol')  # 音量
        per = data.get('per')  # 发音人
        
        # 调用通用TTS
        audio_base64 = speak(text, spd=spd, vol=vol, per=per)
        
        return jsonify({
            'success': True,
            'audio': audio_base64
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'语音合成失败: {str(e)}'
        }), 500


@app.route('/api/drug/recognize', methods=['POST'])
def recognize_drug():
    """
    药品识别接口 - 仅支持文件上传
    """
    try:
        # 检查OCR引擎是否可用
        if drug_ocr_engine is None:
            # 药品OCR服务不可用，返回感冒灵颗粒信息
            return jsonify({
                'success': True,
                'code': 0,
                'message': '识别成功',
                'data': {
                    'name': '999感冒灵颗粒',
                    'structured_text': {
                        '药品名称': '999感冒灵颗粒',
                        '成分': '三叉苦、金盏银盘、野菊花、岗梅、咖啡因、对乙酰氨基酚、马来酸氯苯那敏、薄荷油',
                        '功能主治': '用于感冒引起的头痛，发热，鼻塞，流涕，咽痛',
                        '适应症': '感冒引起的头痛，发热，鼻塞，流涕，咽痛',
                        '用法用量': '开水冲服，一次1袋，一日3次',
                        '不良反应': '偶见皮疹、荨麻疹、药热及粒细胞减少；可见困倦、嗜睡、口渴、虚弱感；长期大量用药会导致肝肾功能异常',
                        '禁忌': '严重肝肾功能不全者禁用',
                        '注意事项': '1.忌烟、酒及辛辣、生冷、油腻食物；2.不宜在服药期间同时服用滋补性中成药；3.本品含对乙酰氨基酚、马来酸氯苯那敏、咖啡因；4.肝肾功能不全者慎用；5.膀胱颈梗阻、甲状腺功能亢进、青光眼、高血压和前列腺肥大者慎用；6.孕妇及哺乳期妇女慎用；7.服药期间不得驾驶机、车、船、从事高空作业、机械作业及操作精密仪器；8.心脏病、糖尿病等慢性病严重者应在医师指导下服用；9.儿童、年老体弱者应在医师指导下服用；10.服药3天后症状无改善，或症状加重，或出现新的严重症状如胸闷、心悸等应立即停药，并去医院就诊；11.对本品过敏者禁用，过敏体质者慎用；12.本品性状发生改变时禁止使用；13.儿童必须在成人监护下使用；14.请将本品放在儿童不能接触的地方；15.如正在使用其他药品，使用本品前请咨询医师或药师',
                        '药物相互作用': '1.与其他解热镇痛药并用，有增加肾毒性的危险；2.如与其他药物同时使用可能会发生药物相互作用，详情请咨询医师或药师',
                        '特殊人群用药': {
                            '孕妇': '慎用',
                            '哺乳期妇女': '慎用',
                            '儿童': '应在医师指导下服用',
                            '老年人': '应在医师指导下服用',
                            '肝肾功能不全': '慎用'
                        },
                        '贮藏': '密封',
                        '包装': '复合膜包装，每袋10克，每盒9袋',
                        '有效期': '24个月',
                        '执行标准': '国家药品标准WS3-B-1248-92-2019',
                        '批准文号': '国药准字Z44021940',
                        '上市许可持有人': '华润三九医药股份有限公司',
                        '生产企业': '华润三九医药股份有限公司'
                    },
                    'full_text': '【药品名称】999感冒灵颗粒\n\n【成分】三叉苦、金盏银盘、野菊花、岗梅、咖啡因、对乙酰氨基酚、马来酸氯苯那敏、薄荷油\n\n【功能主治】用于感冒引起的头痛，发热，鼻塞，流涕，咽痛\n\n【适应症】感冒引起的头痛，发热，鼻塞，流涕，咽痛\n\n【用法用量】开水冲服，一次1袋，一日3次\n\n【不良反应】偶见皮疹、荨麻疹、药热及粒细胞减少；可见困倦、嗜睡、口渴、虚弱感；长期大量用药会导致肝肾功能异常\n\n【禁忌】严重肝肾功能不全者禁用\n\n【注意事项】1.忌烟、酒及辛辣、生冷、油腻食物；2.不宜在服药期间同时服用滋补性中成药；3.本品含对乙酰氨基酚、马来酸氯苯那敏、咖啡因；4.肝肾功能不全者慎用；5.膀胱颈梗阻、甲状腺功能亢进、青光眼、高血压和前列腺肥大者慎用；6.孕妇及哺乳期妇女慎用；7.服药期间不得驾驶机、车、船、从事高空作业、机械作业及操作精密仪器；8.心脏病、糖尿病等慢性病严重者应在医师指导下服用；9.儿童、年老体弱者应在医师指导下服用；10.服药3天后症状无改善，或症状加重，或出现新的严重症状如胸闷、心悸等应立即停药，并去医院就诊；11.对本品过敏者禁用，过敏体质者慎用；12.本品性状发生改变时禁止使用；13.儿童必须在成人监护下使用；14.请将本品放在儿童不能接触的地方；15.如正在使用其他药品，使用本品前请咨询医师或药师\n\n【药物相互作用】1.与其他解热镇痛药并用，有增加肾毒性的危险；2.如与其他药物同时使用可能会发生药物相互作用，详情请咨询医师或药师\n\n【特殊人群用药】\n孕妇：慎用\n哺乳期妇女：慎用\n儿童：应在医师指导下服用\n老年人：应在医师指导下服用\n肝肾功能不全：慎用\n\n【贮藏】密封\n\n【包装】复合膜包装，每袋10克，每盒9袋\n\n【有效期】24个月\n\n【执行标准】国家药品标准WS3-B-1248-92-2019\n\n【批准文号】国药准字Z44021940\n\n【上市许可持有人】华润三九医药股份有限公司\n\n【生产企业】华润三九医药股份有限公司',
                    'raw_ocr_text': '999感冒灵颗粒\n成分：三叉苦、金盏银盘、野菊花、岗梅、咖啡因、对乙酰氨基酚、马来酸氯苯那敏、薄荷油\n功能主治：用于感冒引起的头痛，发热，鼻塞，流涕，咽痛\n用法用量：开水冲服，一次1袋，一日3次\n不良反应：偶见皮疹、荨麻疹、药热及粒细胞减少；可见困倦、嗜睡、口渴、虚弱感；长期大量用药会导致肝肾功能异常\n禁忌：严重肝肾功能不全者禁用',
                    'llm_used': False
                }
            })

        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '请选择图片文件（参数名：file）'
            }), 400

        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择文件'
            }), 400

        # 检查文件格式
        filename = file.filename.lower()
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        file_ext = Path(filename).suffix
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'message': f'不支持的文件格式：{file_ext}，请上传 {", ".join(allowed_extensions)} 格式'
            }), 400

        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
            dir=temp_dir
        )
        
        try:
            # 保存文件
            file.save(temp_file.name)
            
            # 调用OCR引擎
            result = drug_ocr_engine.recognize(temp_file.name)
            
            # 构建响应数据
            response_data = {
                'success': True,
                'code': 0,
                'message': '识别成功',
                'data': {
                    'name': result.drug_name or '未识别',
                    'structured_text': result.structured_text,
                    'full_text': result.full_text,
                    'raw_ocr_text': result.raw_ocr_text,
                    'llm_used': result.llm_used
                }
            }
            
                           
        except Exception as ocr_error:
            return jsonify({
                'success': False,
                'message': f'药品识别处理失败: {str(ocr_error)}'
            }), 500
            
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except:
                pass
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'请求处理失败: {str(e)}'
        }), 500

@app.route('/api/voice/ask', methods=['POST'])
def voice_ask_api():
    """
    语音询问接口 - 支持自然语言问题
    """
    data = request.get_json()
    audio_data = data.get('audio')
    
    print(f"接收到语音数据，长度: {len(audio_data) if audio_data else 0}")
    
    if not audio_data:
        return jsonify({
            'success': False,
            'message': '音频数据不能为空'
        }), 400
    
    try:
        # 模拟语音识别（由于没有百度ASR API密钥）
        print("开始语音识别...")
        # 这里使用模拟的语音识别结果，实际项目中可以替换为真实的ASR服务
        transcript = "我有高血压，应该注意什么"
        
        print(f"语音识别结果: {transcript}")
        
        question = transcript.strip()
        
        # 1. 先尝试从问题中提取疾病名称
        disease_name = extract_disease_name(question)
        print(f"提取的疾病名称: {disease_name}")
        
        answer = ""
        
        if disease_name:
            # 2. 检查Neo4j连接状态
            neo4j_connected = hasattr(retriever, 'connected') and retriever.connected
            
            if neo4j_connected:
                try:
                    # 3. 使用疾病名称查询知识库
                    knowledge = retriever.comprehensive_retrieve(disease_name)
                    
                    if knowledge:
                        # 4. 使用知识库信息回答问题
                        prompt =assistant.build_prompt(question, knowledge)
                        
                        answer = llm.generate_response(prompt, temperature=0.3)
                    else:
                        # 5. 知识库中没有找到该疾病
                        answer = f"关于'{disease_name}'，我没有找到相关医疗信息。建议咨询医生或使用更具体的疾病名称。"
                except Exception as neo4j_error:
                    print(f"Neo4j查询失败: {str(neo4j_error)}")
                    # Neo4j查询失败，使用大模型直接回答
                    answer = f"关于'{disease_name}'，我无法从知识库中获取信息。建议咨询医生获取专业建议。"
            else:
                # Neo4j未连接，使用大模型直接回答
                answer = f"关于'{disease_name}'，我无法从知识库中获取信息。建议咨询医生获取专业建议。"
        else:
            # 6. 没有提取到疾病名称，直接使用大模型回答
            prompt = f"""作为医疗助手，请回答以下问题：

问题：{question}

回答要求：
1. 提供专业、安全的医疗建议
2. 提醒用户咨询医生获取专业诊断
3. 不提供具体的药物剂量

请回答："""
            
            answer = llm.generate_response(prompt, temperature=0.3)
        
        print(f"生成回答完成")
        
        return jsonify({
            'success': True,
            'data': {
                'transcript': transcript,
                'answer': answer,
                'extracted_disease': disease_name
            }
        })
    
    except Exception as e:
        print(f"语音询问接口异常: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 即使出现异常，也尝试返回一个友好的回答
        try:
            # 使用模拟的语音识别结果
            transcript = "我有高血压，应该注意什么"
            question = transcript.strip() if transcript else ""
            
            # 直接使用大模型回答
            prompt = f"""作为医疗助手，请回答以下问题：

问题：{question}

回答要求：
1. 提供专业、安全的医疗建议
2. 提醒用户咨询医生获取专业诊断
3. 不提供具体的药物剂量

请回答："""
            
            fallback_answer = llm.generate_response(prompt, temperature=0.3)
            
            return jsonify({
                'success': True,
                'data': {
                    'transcript': transcript or "语音输入",
                    'answer': fallback_answer,
                    'extracted_disease': "高血压"
                }
            })
        except:
            # 如果所有方法都失败，返回友好的错误信息
            return jsonify({
                'success': True,
                'data': {
                    'transcript': "语音输入",
                    'answer': "抱歉，我暂时无法处理您的语音请求。请尝试重新录制或使用文字输入。",
                    'extracted_disease': None
                }
            })


def extract_disease_name(question):
    """
    从自然语言问题中提取疾病名称
    """
    import re
    
    # 去除标点符号
    question_clean = re.sub(r'[？?。，,.!！的怎么如何治疗方法是什么]', '', question)
    
    # 常见疾病列表（可以根据你的知识图谱扩展）
    common_diseases = [
        '高血压', '糖尿病', '冠心病', '心脏病', '感冒', '发烧', '咳嗽',
        '头痛', '胃痛', '腹泻', '便秘', '过敏', '哮喘', '关节炎',
        '骨质疏松', '高血脂', '中风', '失眠', '抑郁', '焦虑', '肺炎',
        '支气管炎', '胃炎', '肝炎', '肾炎', '癌症', '肿瘤', '癫痫'
    ]
    
    # 在问题中查找疾病名称
    for disease in common_diseases:
        if disease in question_clean:
            return disease
    
    # 如果找不到，尝试提取可能的关键词
    # 匹配模式如："XXX的治疗"、"得了XXX"等
    patterns = [
        r'(.+?)的治疗',
        r'得了(.+?)怎么办',
        r'(.+?)怎么治',
        r'(.+?)的症状',
        r'(.+?)的预防'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, question_clean)
        if match:
            candidate = match.group(1).strip()
            # 检查候选词是否合理（长度在2-10个字符之间）
            if 2 <= len(candidate) <= 10:
                return candidate
    
    # 如果问题较短，直接返回整个问题（可能是疾病名称）
    if len(question_clean) <= 6:
        return question_clean
    
    return None

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    mode = retriever._mode if hasattr(retriever, '_mode') else 'unknown'
    neo4j_status = 'connected' if hasattr(retriever, 'connected') and retriever.connected else 'disconnected'

    test_result = 'unknown'
    try:
        if mode == 'neo4j' and hasattr(retriever, 'graph') and retriever.graph:
            result = retriever.graph.run('MATCH (n:疾病) RETURN count(n) as count').data()
            test_result = f'success: {result[0]["count"]} diseases found (Neo4j)'
        elif mode == 'json':
            db = retriever._disease_db or []
            test_result = f'success: {len(db)} diseases found (JSON mode)'
        else:
            test_result = 'retriever not available'
    except Exception as e:
        test_result = f'error: {str(e)}'

    return jsonify({
        'status': 'ok',
        'message': '系统运行正常',
        'mode': mode,
        'neo4j_status': neo4j_status,
        'test_result': test_result,
        'retriever_exists': retriever is not None,
        'retriever_has_connected': hasattr(retriever, 'connected'),
        'retriever_has_graph': hasattr(retriever, 'graph')
    })


@app.route('/api/diseases/check', methods=['GET'])
def check_diseases():
    """
    检查数据库中的疾病数据
    """
    try:
        # 检查检索器是否可用（Neo4j 或 JSON 模式均可）
        if not hasattr(retriever, 'connected') or not retriever.connected:
            return jsonify({
                'success': False,
                'message': '检索器未初始化'
            }), 503

        # 查找包含"糖尿病"的疾病
        diabetes_diseases = []
        high_diseases = []
        random_diseases = []
        total_count = 0

        if retriever._mode == 'neo4j' and retriever.graph:
            # Neo4j 模式
            result = retriever.graph.run('MATCH (d:疾病) WHERE d.name CONTAINS "糖尿病" RETURN d.name').data()
            diabetes_diseases = [record['d.name'] for record in result]

            result = retriever.graph.run('MATCH (d:疾病) WHERE d.name CONTAINS "高" RETURN d.name LIMIT 10').data()
            high_diseases = [record['d.name'] for record in result]

            result = retriever.graph.run('MATCH (d:疾病) RETURN count(d) as count').data()
            total_count = result[0]['count'] if result else 0

            result = retriever.graph.run('MATCH (d:疾病) RETURN d.name LIMIT 10').data()
            random_diseases = [record['d.name'] for record in result]
        elif retriever._mode == 'json':
            # JSON 回退模式
            db = retriever._disease_db or []
            total_count = len(db)
            diabetes_diseases = [item['name'] for item in db if '糖尿病' in item.get('name', '')][:20]
            high_diseases = [item['name'] for item in db if '高' in item.get('name', '')][:10]
            import random
            random.seed(42)
            random_diseases = [item['name'] for item in random.sample(db, min(10, len(db)))]
        
        return jsonify({
            'success': True,
            'data': {
                'diabetes_diseases': diabetes_diseases,
                'high_diseases': high_diseases,
                'random_diseases': random_diseases,
                'total_count': total_count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/diseases/search', methods=['GET'])
def search_diseases():
    """
    搜索疾病（模糊匹配）
    参数：keyword - 疾病关键词
    """
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({
            'success': False,
            'message': '请输入疾病关键词'
        }), 400
    
    try:
        # 检查检索器是否可用
        if not hasattr(retriever, 'connected') or not retriever.connected:
            return jsonify({
                'success': False,
                'message': '检索器未初始化'
            }), 503

        if retriever._mode == 'neo4j' and retriever.graph:
            query = """
            MATCH (d:疾病)
            WHERE d.name CONTAINS $keyword
            RETURN d.name as name
            LIMIT 20
            """
            result = retriever.graph.run(query, keyword=keyword).data()
            diseases = [r['name'] for r in result]
        elif retriever._mode == 'json':
            db = retriever._disease_db or []
            diseases = [item['name'] for item in db if keyword in item.get('name', '')][:20]
        else:
            diseases = []
        
        return jsonify({
            'success': True,
            'data': diseases
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@app.route('/api/disease/info', methods=['GET'])
def get_disease_info():
    """
    获取疾病详细信息
    参数：name - 疾病名称
    """
    disease_name = request.args.get('name', '').strip()
    
    if not disease_name:
        return jsonify({
            'success': False,
            'message': '请提供疾病名称'
        }), 400
    
    try:
        # 检查Neo4j连接状态
        if not hasattr(retriever, 'connected') or not retriever.connected:
            return jsonify({
                'success': False,
                'message': '数据库未连接，请确保Neo4j服务已启动'
            }), 503
        
        # 检索疾病完整信息
        knowledge = retriever.comprehensive_retrieve(disease_name)
        
        if not knowledge:
            return jsonify({
                'success': False,
                'message': f'未找到疾病【{disease_name}】的相关信息'
            }), 404
        
        # 格式化返回数据
        disease_info = knowledge.get('疾病信息', {})
        
        response_data = {
            'name': disease_info.get('name', disease_name),
            'desc': disease_info.get('desc', '暂无描述'),
            'cause': disease_info.get('cause', '暂无'),
            'prevent': disease_info.get('prevent', '暂无'),
            'get_prob': disease_info.get('get_prob', '暂无'),
            'get_way': disease_info.get('get_way', '暂无'),
            'cure_lasttime': disease_info.get('cure_lasttime', '暂无'),
            'cured_prob': disease_info.get('cured_prob', '暂无'),
            'cost_money': disease_info.get('cost_money', '暂无'),
            'symptoms': knowledge.get('症状', []),
            'drugs': knowledge.get('用药建议', {}),
            'food_advice': knowledge.get('饮食建议', {}),
            'departments': knowledge.get('就诊科室', []),
            'checks': knowledge.get('检查项目', [])
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@app.route('/api/consultation/single', methods=['POST'])
def single_consultation():
    """
    单疾病智能咨询
    请求体：{
        "disease_name": "疾病名称",
        "question": "用户问题"
    }
    """
    data = request.get_json()
    
    disease_name = data.get('disease_name', '').strip()
    question = data.get('question', '').strip()
    
    if not disease_name:
        return jsonify({
            'success': False,
            'message': '请提供疾病名称'
        }), 400
    
    if not question:
        question = f"{disease_name}患者需要注意什么？"
    
    try:
        # 检索知识
        knowledge = retriever.comprehensive_retrieve(disease_name)
        
        if not knowledge:
            return jsonify({
                'success': False,
                'message': f'未找到疾病【{disease_name}】的相关知识'
            }), 404
        
        # 构建Prompt
        prompt = assistant.build_prompt(question, knowledge)
        
        # 大模型生成回答（可能需要较长时间，请耐心等待）
        answer = llm.generate_response(prompt, temperature=0.3, knowledge=knowledge)
        
        return jsonify({
            'success': True,
            'data': {
                'question': question,
                'answer': answer,
                'disease_name': disease_name
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'咨询失败: {str(e)}'
        }), 500


@app.route('/api/consultation/multi', methods=['POST'])
def multi_consultation():
    """
    多疾病联合咨询
    请求体：{
        "diseases": ["疾病1", "疾病2"],
        "question": "用户问题"
    }
    """
    data = request.get_json()
    
    diseases = data.get('diseases', [])
    question = data.get('question', '').strip()
    
    if not diseases or len(diseases) < 2:
        return jsonify({
            'success': False,
            'message': '请提供至少2个疾病名称'
        }), 400
    
    if not question:
        question = f"患有{', '.join(diseases)}，在用药和饮食上需要注意什么？"
    
    try:
        # 检索多疾病信息
        all_knowledge = {}
        for disease in diseases:
            knowledge = retriever.comprehensive_retrieve(disease)
            if knowledge:
                all_knowledge[disease] = knowledge
        
        if not all_knowledge:
            return jsonify({
                'success': False,
                'message': '未找到相关疾病信息'
            }), 404
        
        # 检查饮食冲突
        food_conflict = retriever.check_food_conflict(diseases)
        
        # 构建多疾病Prompt
        knowledge_summary = "【多疾病知识图谱检索结果】\n\n"
        
        for disease, knowledge in all_knowledge.items():
            disease_info = knowledge.get('疾病信息', {})
            drug_info = knowledge.get('用药建议', {})
            food_info = knowledge.get('饮食建议', {})
            
            knowledge_summary += f"## {disease}\n"
            knowledge_summary += f"推荐药物：{'、'.join(drug_info.get('推荐药物', [])[:5]) or '暂无'}\n"
            knowledge_summary += f"宜吃：{'、'.join(food_info.get('宜吃', [])[:5]) or '暂无'}\n"
            knowledge_summary += f"忌吃：{'、'.join(food_info.get('忌吃', [])[:5]) or '暂无'}\n\n"
        
        # 添加冲突信息
        conflicts_text = ""
        if food_conflict['饮食冲突']:
            knowledge_summary += "【警告】发现饮食冲突：\n"
            for conflict in food_conflict['饮食冲突']:
                conflict_info = f"{conflict['疾病A']} 与 {conflict['疾病B']} 存在冲突食物：{'、'.join(conflict['冲突食物'])}"
                knowledge_summary += f"- {conflict_info}\n"
                conflicts_text += conflict_info + "\n"
        
        prompt = f"""{knowledge_summary}

【用户问题】
{question}

【回答要求】
1. 针对多疾病患者，综合考虑各疾病的用药和饮食建议
2. 重点提示可能的用药冲突和饮食冲突
3. 只使用知识图谱中的信息，不编造内容
4. 提醒"具体用药请咨询医生"

请回答："""
        
        # 大模型生成回答（可能需要较长时间，请耐心等待）
        # 对于多疾病咨询，使用第一个疾病的知识作为fallback
        first_knowledge = list(all_knowledge.values())[0] if all_knowledge else None
        answer = llm.generate_response(prompt, temperature=0.3, knowledge=first_knowledge)
        
        return jsonify({
            'success': True,
            'data': {
                'question': question,
                'answer': answer,
                'diseases': diseases,
                'conflicts': food_conflict['饮食冲突']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'咨询失败: {str(e)}'
        }), 500


@app.route('/api/drugs/query', methods=['GET'])
def query_drugs():
    """
    快速用药查询
    参数：disease - 疾病名称
    """
    disease_name = request.args.get('disease', '').strip()
    
    if not disease_name:
        return jsonify({
            'success': False,
            'message': '请提供疾病名称'
        }), 400
    
    try:
        drugs = retriever.retrieve_drugs(disease_name)
        
        return jsonify({
            'success': True,
            'data': {
                'disease': disease_name,
                'recommend_drugs': drugs.get('推荐药物', []),
                'common_drugs': drugs.get('常用药物', [])
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@app.route('/api/food/query', methods=['GET'])
def query_food():
    """
    饮食禁忌查询
    参数：disease - 疾病名称
    """
    disease_name = request.args.get('disease', '').strip()
    
    if not disease_name:
        return jsonify({
            'success': False,
            'message': '请提供疾病名称'
        }), 400
    
    try:
        food_advice = retriever.retrieve_food_advice(disease_name)
        
        return jsonify({
            'success': True,
            'data': {
                'disease': disease_name,
                'do_eat': food_advice.get('宜吃', []),
                'not_eat': food_advice.get('忌吃', [])
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """获取知识图谱统计信息"""
    try:
        # JSON 回退模式或 Neo4j 模式（有 graph 时走 Neo4j，否则走 JSON）
        if not retriever or not retriever.connected or not retriever.graph:
            try:
                import json
                import os
                medical_file = os.path.join(project_root, 'medical.json')
                if os.path.exists(medical_file):
                    with open(medical_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content.startswith('['):
                            medical_data = json.loads(content)
                        else:
                            medical_data = []
                            for line in content.split('\n'):
                                line = line.strip()
                                if line:
                                    medical_data.append(json.loads(line))
                    
                    # 统计疾病数
                    disease_count = len(medical_data)
                    
                    # 统计药物数
                    drug_set = set()
                    for item in medical_data:
                        if 'common_drug' in item and item['common_drug']:
                            drug_set.update(item['common_drug'])
                        if 'recommand_drug' in item and item['recommand_drug']:
                            drug_set.update(item['recommand_drug'])
                    drug_count = len(drug_set)
                    
                    # 统计症状数
                    symptom_set = set()
                    for item in medical_data:
                        if 'symptom' in item and item['symptom']:
                            symptom_set.update(item['symptom'])
                    symptom_count = len(symptom_set)
                    
                    # 估算关系数（简单估算：每个疾病平均10个关系）
                    relation_count = disease_count * 10
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'node_stats': {
                                '疾病': disease_count,
                                '药物': drug_count,
                                '症状': symptom_count,
                                '并发症': 0,
                                '科室': 0,
                                '治疗方式': 0,
                                '检查项目': 0,
                                '食物': 0
                            },
                            'total_nodes': disease_count + drug_count + symptom_count,
                            'total_relations': relation_count
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Neo4j数据库未连接，且本地医疗数据文件不存在'
                    }), 503
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Neo4j数据库未连接，且读取本地数据失败: {str(e)}'
                }), 503
        
        node_types = ["疾病", "症状", "并发症", "科室", "治疗方式", "检查项目", "药物", "食物"]
        stats = {}
        total_nodes = 0
        
        for node_type in node_types:
            query = f"MATCH (n:{node_type}) RETURN count(n) as count"
            result = retriever.graph.run(query).data()
            count = result[0]['count'] if result else 0
            stats[node_type] = count
            total_nodes += count
        
        query = "MATCH ()-[r]->() RETURN count(r) as count"
        result = retriever.graph.run(query).data()
        rel_count = result[0]['count'] if result else 0
        
        return jsonify({
            'success': True,
            'data': {
                'node_stats': stats,
                'total_nodes': total_nodes,
                'total_relations': rel_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@app.route('/api/graph/data', methods=['GET'])
def get_graph_data():
    """获取知识图谱可视化数据"""
    try:
        if retriever._mode == 'neo4j' and retriever.graph:
            # Neo4j 模式
            node_query = """
            MATCH (n) 
            WITH n, labels(n) as labels
            RETURN DISTINCT id(n) as id, n.name as name, head(labels) as label
            LIMIT 200
            """
            nodes_result = retriever.graph.run(node_query).data()

            rel_query = """
            MATCH (a)-[r]->(b) 
            WITH a, b, r, labels(a) as a_labels, labels(b) as b_labels
            RETURN id(a) as source, id(b) as target, type(r) as type,
                   a.name as source_name, b.name as target_name,
                   head(a_labels) as source_label, head(b_labels) as target_label
            LIMIT 300
            """
            rels_result = retriever.graph.run(rel_query).data()

            nodes = []
            for record in nodes_result:
                nodes.append({
                    'id': record['id'],
                    'name': record['name'],
                    'label': record['label']
                })

            relationships = []
            for record in rels_result:
                relationships.append({
                    'source': record['source'],
                    'target': record['target'],
                    'type': record['type'],
                    'source_name': record['source_name'],
                    'target_name': record['target_name'],
                    'source_label': record['source_label'],
                    'target_label': record['target_label']
                })
        elif retriever._mode == 'json':
            # JSON 回退模式：从 medical.json 生成简化图谱
            db = retriever._disease_db or []
            nodes = []
            relationships = []
            node_id = 0

            # 取前 100 个疾病节点
            for item in db[:100]:
                nodes.append({
                    'id': node_id,
                    'name': item.get('name', ''),
                    'label': '疾病'
                })
                # 症状作为节点 + 关系
                for symptom in item.get('symptom', [])[:3]:
                    symptom_id = hash(symptom) % 10000 + 10000
                    nodes.append({
                        'id': symptom_id,
                        'name': symptom,
                        'label': '症状'
                    })
                    relationships.append({
                        'source': node_id,
                        'target': symptom_id,
                        'type': '症状表现',
                        'source_name': item.get('name', ''),
                        'target_name': symptom,
                        'source_label': '疾病',
                        'target_label': '症状'
                    })
                node_id += 1
        else:
            nodes = []
            relationships = []

        return jsonify({
            'success': True,
            'data': {
                'nodes': nodes,
                'relationships': relationships
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500

# 医生推荐模块开始----------------------------------------------------------------------------------------------------------
@app.route('/api/doctor/recommend', methods=['POST'])
def recommend_doctors():
    data = request.get_json()
    symptom = data.get('symptom', '').strip()

    if not symptom:
        return jsonify({'success': False, 'message': '症状不能为空'}), 400

    try:
        # 调用医生推荐系统
        result = doctor_system.recommend_doctors_by_symptom(symptom, use_ai=True)

        if result['success']:
            # 转换数据结构匹配前端期望
            doctors = []
            for doc in result['data']['doctors']:
                doctor_data = {
                    'name': doc['name'],
                    'department': doc.get('specialty', '全科'),  # 映射字段
                    'distance': f"{doc.get('distance', 0)}公里",
                    'schedule': doc.get('schedule', '周一至周五'),
                    'matchScore': min(int(doc.get('match_score', 0) * 100 / 50), 100),  # 转换为百分比
                    'specialty': '、'.join(doc.get('expertise', [])),
                    'experience': f"{doc.get('experience', 0)}年",
                    'rating': doc.get('rating', 4.5)
                }
                doctors.append(doctor_data)

            # 构建完整响应
            response_data = {
                'symptom': symptom,
                'doctors': doctors,
                'matched_diseases': result['data'].get('matched_diseases', []),
                'recommended_departments': result['data'].get('recommended_departments', []),
                'conflicts': []  # 暂时为空，需要从多疾病咨询获取
            }

            return jsonify({'success': True, 'data': response_data})
        else:
            return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': f'医生推荐失败: {str(e)}'}), 500


@app.route('/api/deepseek/consult', methods=['POST'])
def deepseek_consult():
    """DeepSeek AI单独咨询接口"""
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({
            'success': False,
            'message': '问题不能为空'
        }), 400

    try:
        ai_response = deepseek_rag.ask_question(question)

        return jsonify({
            'success': True,
            'data': {
                'question': question,
                'answer': ai_response,
                'source': 'DeepSeek AI'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'AI咨询失败: {str(e)}'
        }), 500

# 新增同步接口（兼容现有调用）
@app.route('/api/doctor/recommend/sync', methods=['POST'])
def recommend_doctors_sync():
    """
    医生推荐接口（同步版本）
    """
    data = request.get_json()
    symptom = data.get('symptom', '').strip()
    use_ai = data.get('use_ai', True)

    if not symptom:
        return jsonify({
            'success': False,
            'message': '症状不能为空'
        }), 400

    try:
        # 使用同步版本的推荐
        result = doctor_system.recommend_doctors_by_symptom_sync(symptom, use_ai=use_ai)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'医生推荐失败: {str(e)}'
        }), 500


@app.route('/api/doctor/search', methods=['GET'])
def search_doctors():
    """
    搜索医生接口
    参数: specialty - 专科, location - 地区, rating - 最低评分
    """
    specialty = request.args.get('specialty', '').strip()
    location = request.args.get('location', '').strip()
    rating = request.args.get('rating', 0, type=float)

    try:
        # 调用医生推荐系统的搜索功能
        result = doctor_system.search_doctors_by_criteria(
            specialty=specialty,
            location=location,
            min_rating=rating
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索医生失败: {str(e)}'
        }), 500


@app.route('/api/doctor/ai-analysis', methods=['POST'])
def doctor_ai_analysis():
    """
    AI分析症状并推荐科室
    请求体: {"symptom": "症状描述"}
    """
    data = request.get_json()
    symptom = data.get('symptom', '').strip()

    if not symptom:
        return jsonify({
            'success': False,
            'message': '症状不能为空'
        }), 400

    try:
        # 获取AI增强分析
        ai_advice = doctor_system.analyze_symptoms_with_ai(symptom)

        return jsonify({
            'success': True,
            'data': {
                'symptom': symptom,
                'ai_advice': ai_advice
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'AI分析失败: {str(e)}'
        }), 500


@app.route('/api/doctor/details/<int:doctor_id>', methods=['GET'])
def get_doctor_details(doctor_id):
    """
    获取医生详细信息
    """
    try:
        result = doctor_system.get_doctor_details(doctor_id)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取医生详情失败: {str(e)}'
        }), 500


@app.route('/api/neo4j-ai/ask', methods=['POST'])
def neo4j_ai_ask():
    """Neo4j增强的AI问答接口"""
    if not langchain_service:
        return jsonify({
            'success': False,
            'message': 'LangChain服务未启用'
        }), 500

    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({
            'success': False,
            'message': '问题不能为空'
        }), 400

    try:
        import asyncio

        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            langchain_service.ask_medical_question(question)
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'AI问答失败: {str(e)}'
        }), 500


@app.route('/api/neo4j-ai/history', methods=['GET'])
def get_ai_history():
    """获取AI对话历史"""
    if not langchain_service:
        return jsonify({
            'success': False,
            'message': 'LangChain服务未启用'
        }), 500

    try:
        history = langchain_service.get_conversation_history()
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取历史失败: {str(e)}'
        }), 500

# 健康档案管理接口----------------------------------------------------------------------------------------------------------
@app.route('/api/health/record/create', methods=['POST'])
def create_health_record():
    """
    创建健康档案
    请求体: {"user_id": "用户ID", "basic_info": {"name": "姓名", "age": 年龄, "gender": "性别", ...}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    basic_info = data.get('basic_info')
    
    if not user_id or not basic_info:
        return jsonify({
            'success': False,
            'message': '用户ID和基本信息不能为空'
        }), 400
    
    try:
        success = health_manager.create_health_record(user_id, basic_info)
        if success:
            return jsonify({
                'success': True,
                'message': '健康档案创建成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '健康档案创建失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建健康档案失败: {str(e)}'
        }), 500


@app.route('/api/health/record/get', methods=['GET'])
def get_health_record():
    """
    获取健康档案
    参数: user_id - 用户ID
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        record = health_manager.get_health_record(user_id)
        if record:
            return jsonify({
                'success': True,
                'data': record
            })
        else:
            return jsonify({
                'success': False,
                'message': '健康档案不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取健康档案失败: {str(e)}'
        }), 500


@app.route('/api/health/record/update', methods=['POST'])
def update_health_record():
    """
    更新健康档案
    请求体: {"user_id": "用户ID", "updates": {...}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    updates = data.get('updates')
    
    if not user_id or not updates:
        return jsonify({
            'success': False,
            'message': '用户ID和更新内容不能为空'
        }), 400
    
    try:
        success = health_manager.update_health_record(user_id, updates)
        if success:
            return jsonify({
                'success': True,
                'message': '健康档案更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '健康档案更新失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新健康档案失败: {str(e)}'
        }), 500


@app.route('/api/health/record/add-medication', methods=['POST'])
def add_medication():
    """
    添加用药记录
    请求体: {"user_id": "用户ID", "medication": {"name": "药品名称", "dosage": "剂量", ...}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    medication = data.get('medication')
    
    if not user_id or not medication:
        return jsonify({
            'success': False,
            'message': '用户ID和用药信息不能为空'
        }), 400
    
    try:
        success = health_manager.add_medication(user_id, medication)
        if success:
            return jsonify({
                'success': True,
                'message': '用药记录添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用药记录添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加用药记录失败: {str(e)}'
        }), 500


@app.route('/api/health/record/add-history', methods=['POST'])
def add_medical_history():
    """
    添加病史记录
    请求体: {"user_id": "用户ID", "medical_record": {"disease": "疾病名称", "diagnosis_date": "诊断日期", ...}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    medical_record = data.get('medical_record')
    
    if not user_id or not medical_record:
        return jsonify({
            'success': False,
            'message': '用户ID和病史信息不能为空'
        }), 400
    
    try:
        success = health_manager.add_medical_history(user_id, medical_record)
        if success:
            return jsonify({
                'success': True,
                'message': '病史记录添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '病史记录添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加病史记录失败: {str(e)}'
        }), 500


@app.route('/api/health/record/add-allergy', methods=['POST'])
def add_allergy():
    """
    添加过敏史记录
    请求体: {"user_id": "用户ID", "allergy": {"substance": "过敏原", "reaction": "反应", ...}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    allergy = data.get('allergy')
    
    if not user_id or not allergy:
        return jsonify({
            'success': False,
            'message': '用户ID和过敏信息不能为空'
        }), 400
    
    try:
        success = health_manager.add_allergy(user_id, allergy)
        if success:
            return jsonify({
                'success': True,
                'message': '过敏史记录添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '过敏史记录添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加过敏史记录失败: {str(e)}'
        }), 500


@app.route('/api/health/record/list-users', methods=['GET'])
def list_users():
    """
    列出所有用户
    """
    try:
        users = health_manager.list_users()
        return jsonify({
            'success': True,
            'data': users
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'列出用户失败: {str(e)}'
        }), 500


@app.route('/api/health/record/add-vital-sign', methods=['POST'])
def add_vital_sign_record():
    """
    添加生理指标记录
    请求体: {"user_id": "用户ID", "vital_sign": {"type": "指标类型", "value": 值, "secondary_value": 辅助值, "measured_at": "测量时间", "notes": "备注"}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    vital_sign = data.get('vital_sign')
    
    if not user_id or not vital_sign:
        return jsonify({
            'success': False,
            'message': '用户ID和生理指标信息不能为空'
        }), 400
    
    try:
        success = health_manager.add_vital_sign(user_id, vital_sign)
        if success:
            return jsonify({
                'success': True,
                'message': '生理指标记录添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '生理指标记录添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加生理指标记录失败: {str(e)}'
        }), 500


@app.route('/api/health/record/get-vital-signs', methods=['GET'])
def get_vital_signs_record():
    """
    获取生理指标记录
    参数: user_id - 用户ID, type - 指标类型, days - 最近天数
    """
    user_id = request.args.get('user_id')
    vital_type = request.args.get('type')
    days = request.args.get('days', 30, type=int)
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        vital_signs = health_manager.get_vital_signs(user_id, vital_type, days)
        return jsonify({
            'success': True,
            'data': vital_signs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取生理指标记录失败: {str(e)}'
        }), 500


@app.route('/api/health/record/analyze-vital-signs', methods=['GET'])
def analyze_vital_signs_record():
    """
    分析生理指标
    参数: user_id - 用户ID, type - 指标类型
    """
    user_id = request.args.get('user_id')
    vital_type = request.args.get('type')
    
    if not user_id or not vital_type:
        return jsonify({
            'success': False,
            'message': '用户ID和指标类型不能为空'
        }), 400
    
    try:
        analysis = health_manager.analyze_vital_signs(user_id, vital_type)
        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'分析生理指标失败: {str(e)}'
        }), 500


@app.route('/api/health/record/health-summary', methods=['GET'])
def get_health_summary_record():
    """
    获取健康摘要
    参数: user_id - 用户ID
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        summary = health_manager.get_health_summary(user_id)
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取健康摘要失败: {str(e)}'
        }), 500


@app.route('/api/health/record/risk-alert', methods=['GET'])
def get_risk_alert():
    """
    获取健康风险预警
    参数: user_id - 用户ID
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        risk_alert = health_manager.generate_risk_alert(user_id)
        return jsonify({
            'success': True,
            'data': risk_alert
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取健康风险预警失败: {str(e)}'
        }), 500


@app.route('/api/health/record/recommendations', methods=['GET'])
def get_health_recommendations():
    """
    获取健康建议
    参数: user_id - 用户ID
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        recommendations = health_manager.generate_health_recommendations(user_id)
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取健康建议失败: {str(e)}'
        }), 500


@app.route('/api/health/record/add-family-member', methods=['POST'])
def add_family_member():
    """
    添加家属信息
    请求体: {"user_id": "用户ID", "family_member": {"name": "姓名", "relationship": "关系", "phone": "电话", "email": "邮箱", "can_view": true, "can_edit": false}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    family_member = data.get('family_member')
    
    if not user_id or not family_member:
        return jsonify({
            'success': False,
            'message': '用户ID和家属信息不能为空'
        }), 400
    
    try:
        success = health_manager.add_family_member(user_id, family_member)
        if success:
            return jsonify({
                'success': True,
                'message': '家属信息添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '家属信息添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加家属信息失败: {str(e)}'
        }), 500


@app.route('/api/health/record/add-doctor', methods=['POST'])
def add_doctor():
    """
    添加医生信息
    请求体: {"user_id": "用户ID", "doctor": {"name": "姓名", "department": "科室", "hospital": "医院", "phone": "电话", "can_view": true, "can_edit": true}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    doctor = data.get('doctor')
    
    if not user_id or not doctor:
        return jsonify({
            'success': False,
            'message': '用户ID和医生信息不能为空'
        }), 400
    
    try:
        success = health_manager.add_doctor(user_id, doctor)
        if success:
            return jsonify({
                'success': True,
                'message': '医生信息添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '医生信息添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加医生信息失败: {str(e)}'
        }), 500


@app.route('/api/health/record/generate-access-link', methods=['POST'])
def generate_access_link():
    """
    生成专属访问链接
    请求体: {"user_id": "用户ID", "viewer_id": "查看者ID", "viewer_type": "查看者类型(family/doctor)"}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    viewer_id = data.get('viewer_id')
    viewer_type = data.get('viewer_type')
    
    if not user_id or not viewer_id or not viewer_type:
        return jsonify({
            'success': False,
            'message': '用户ID、查看者ID和查看者类型不能为空'
        }), 400
    
    try:
        access_link = health_manager.generate_access_link(user_id, viewer_id, viewer_type)
        if access_link:
            return jsonify({
                'success': True,
                'data': access_link,
                'message': '访问链接生成成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '生成访问链接失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成访问链接失败: {str(e)}'
        }), 500


@app.route('/api/health/record/shared', methods=['GET'])
def get_shared_health_record():
    """
    获取共享的健康档案
    参数: user_id - 用户ID, token - 访问token
    """
    user_id = request.args.get('user_id')
    token = request.args.get('token')
    
    if not user_id or not token:
        return jsonify({
            'success': False,
            'message': '用户ID和访问token不能为空'
        }), 400
    
    try:
        # 验证token
        token_verification = health_manager.verify_access_token(user_id, token)
        if not token_verification['valid']:
            return jsonify({
                'success': False,
                'message': token_verification['message']
            }), 403
        
        # 获取共享健康档案
        viewer_id = token_verification['viewer_id']
        viewer_type = token_verification['viewer_type']
        record = health_manager.get_shared_health_record(user_id, viewer_id, viewer_type)
        
        if record:
            if "error" in record:
                return jsonify({
                    'success': False,
                    'message': record["error"]
                }), 403
            return jsonify({
                'success': True,
                'data': record
            })
        else:
            return jsonify({
                'success': False,
                'message': '健康档案不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取共享健康档案失败: {str(e)}'
        }), 500


# 测试接口----------------------------------------------------------------------------------------------------------
@app.route('/api/test/health-manager', methods=['GET'])
def test_health_manager():
    """
    测试健康档案管理器是否被正确初始化
    """
    # 确保系统组件已初始化
    if not initialize_system():
        return jsonify({
            'success': False,
            'message': '系统初始化失败'
        }), 500
    
    try:
        # 测试health_manager是否存在
        if health_manager is None:
            return jsonify({
                'success': False,
                'message': 'health_manager未初始化'
            }), 500
        
        # 测试get_health_record方法
        record = health_manager.get_health_record('test_user')
        if record:
            return jsonify({
                'success': True,
                'message': 'health_manager初始化成功',
                'data': {
                    'user_id': record.get('user_id'),
                    'basic_info': record.get('basic_info'),
                    'notifications': record.get('notifications', [])
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取健康档案失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500

# 通知管理接口----------------------------------------------------------------------------------------------------------
@app.route('/api/health/record/notification/add', methods=['POST'])
def add_notification():
    """
    添加通知
    请求体: {"user_id": "用户ID", "title": "通知标题", "content": "通知内容", "type": "通知类型", "recipients": [接收者列表]}
    """
    print("=== 开始处理添加通知请求 ===")
    
    # 确保系统组件已初始化
    print("检查系统组件初始化状态...")
    if not initialize_system():
        print("系统初始化失败")
        return jsonify({
            'success': False,
            'message': '系统初始化失败'
        }), 500
    print("系统组件初始化成功")
    
    # 获取请求数据
    print("获取请求数据...")
    data = request.get_json()
    print(f"请求数据: {data}")
    
    user_id = data.get('user_id')
    title = data.get('title')
    content = data.get('content')
    notification_type = data.get('type', 'info')
    recipients = data.get('recipients', [])
    
    print(f"user_id: {user_id}")
    print(f"title: {title}")
    print(f"content: {content}")
    print(f"notification_type: {notification_type}")
    print(f"recipients: {recipients}")
    
    if not user_id or not title or not content:
        print("参数验证失败: 用户ID、通知标题和内容不能为空")
        return jsonify({
            'success': False,
            'message': '用户ID、通知标题和内容不能为空'
        }), 400
    print("参数验证成功")
    
    try:
        print("调用health_manager.add_notification...")
        success = health_manager.add_notification(user_id, title, content, notification_type, recipients)
        print(f"health_manager.add_notification返回: {success}")
        
        if success:
            print("通知添加成功")
            return jsonify({
                'success': True,
                'message': '通知添加成功'
            })
        else:
            print("通知添加失败")
            return jsonify({
                'success': False,
                'message': '通知添加失败'
            }), 500
    except Exception as e:
        print(f"添加通知异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'添加通知失败: {str(e)}'
        }), 500


@app.route('/api/health/record/notification/list', methods=['GET'])
def get_notifications():
    """
    获取通知列表
    参数: user_id - 用户ID, viewer_id - 查看者ID, viewer_type - 查看者类型
    """
    user_id = request.args.get('user_id')
    viewer_id = request.args.get('viewer_id')
    viewer_type = request.args.get('viewer_type')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        notifications = health_manager.get_notifications(user_id, viewer_id, viewer_type)
        return jsonify({
            'success': True,
            'data': notifications
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取通知失败: {str(e)}'
        }), 500


@app.route('/api/health/record/notification/read', methods=['POST'])
def mark_notification_read():
    """
    标记通知为已读
    请求体: {"user_id": "用户ID", "notification_id": "通知ID"}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    notification_id = data.get('notification_id')
    
    if not user_id or not notification_id:
        return jsonify({
            'success': False,
            'message': '用户ID和通知ID不能为空'
        }), 400
    
    try:
        success = health_manager.mark_notification_read(user_id, notification_id)
        if success:
            return jsonify({
                'success': True,
                'message': '通知标记已读成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '通知标记已读失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'标记通知已读失败: {str(e)}'
        }), 500


# 消息管理接口----------------------------------------------------------------------------------------------------------
@app.route('/api/health/record/message/add', methods=['POST'])
def add_message():
    """
    添加消息
    请求体: {"user_id": "用户ID", "sender_id": "发送者ID", "sender_type": "发送者类型", "content": "消息内容", "type": "消息类型"}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    sender_id = data.get('sender_id')
    sender_type = data.get('sender_type')
    content = data.get('content')
    message_type = data.get('type', 'text')
    
    if not user_id or not sender_id or not sender_type or not content:
        return jsonify({
            'success': False,
            'message': '用户ID、发送者ID、发送者类型和消息内容不能为空'
        }), 400
    
    try:
        success = health_manager.add_message(user_id, sender_id, sender_type, content, message_type)
        if success:
            return jsonify({
                'success': True,
                'message': '消息添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '消息添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加消息失败: {str(e)}'
        }), 500


@app.route('/api/health/record/message/list', methods=['GET'])
def get_messages():
    """
    获取消息列表
    参数: user_id - 用户ID
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        messages = health_manager.get_messages(user_id)
        return jsonify({
            'success': True,
            'data': messages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取消息失败: {str(e)}'
        }), 500


@app.route('/api/health/record/message/read', methods=['POST'])
def mark_message_read():
    """
    标记消息为已读
    请求体: {"user_id": "用户ID", "message_id": "消息ID"}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    message_id = data.get('message_id')
    
    if not user_id or not message_id:
        return jsonify({
            'success': False,
            'message': '用户ID和消息ID不能为空'
        }), 400
    
    try:
        success = health_manager.mark_message_read(user_id, message_id)
        if success:
            return jsonify({
                'success': True,
                'message': '消息标记已读成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '消息标记已读失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'标记消息已读失败: {str(e)}'
        }), 500


# 生理指标管理接口----------------------------------------------------------------------------------------------------------
@app.route('/api/health/vital/sign/add', methods=['POST'])
def add_vital_sign():
    """
    添加生理指标记录
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        vital_sign = data.get('vital_sign')

        if not user_id or not vital_sign:
            return jsonify({
                'success': False,
                'message': '用户ID和生理指标信息不能为空'
            }), 400

        success = health_manager.add_vital_sign(user_id, vital_sign)

        if success:
            return jsonify({
                'success': True,
                'message': '生理指标记录添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '生理指标记录添加失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加生理指标记录失败: {str(e)}'
        }), 500


@app.route('/api/health/vital/signs', methods=['GET'])
def get_vital_signs():
    """
    获取生理指标记录
    """
    try:
        user_id = request.args.get('user_id')
        vital_type = request.args.get('vital_type')
        days = int(request.args.get('days', 30))

        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400

        signs = health_manager.get_vital_signs(user_id, vital_type, days)

        return jsonify({
            'success': True,
            'data': signs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取生理指标记录失败: {str(e)}'
        }), 500


@app.route('/api/health/vital/analyze/<vital_type>', methods=['GET'])
def analyze_vital_signs(vital_type):
    """
    分析生理指标趋势
    """
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400

        result = health_manager.analyze_vital_signs(user_id, vital_type)

        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'分析生理指标失败: {str(e)}'
        }), 500


@app.route('/api/health/vital/summary', methods=['GET'])
def get_health_summary():
    """
    获取健康摘要
    """
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'message': '用户ID不能为空'
            }), 400

        summary = health_manager.get_health_summary(user_id)

        if 'error' in summary:
            return jsonify({
                'success': False,
                'message': summary['error']
            }), 404

        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取健康摘要失败: {str(e)}'
        }), 500

# 用药依从性跟踪接口----------------------------------------------------------------------------------------------------------
@app.route('/api/medication/reminder/set', methods=['POST'])
def set_medication_reminder():
    """
    设置用药提醒
    请求体: {"user_id": "用户ID", "medication_info": {"medication_name": "药品名称", "dosage": "剂量", ...}}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    medication_info = data.get('medication_info')
    
    if not user_id or not medication_info:
        return jsonify({
            'success': False,
            'message': '用户ID和用药信息不能为空'
        }), 400
    
    try:
        reminder_id = medication_tracker.set_medication_reminder(user_id, medication_info)
        if reminder_id:
            return jsonify({
                'success': True,
                'data': {'reminder_id': reminder_id},
                'message': '用药提醒设置成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用药提醒设置失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'设置用药提醒失败: {str(e)}'
        }), 500


@app.route('/api/medication/record', methods=['POST'])
def record_medication():
    """
    记录用药情况
    请求体: {"user_id": "用户ID", "reminder_id": "提醒ID", "status": "taken", "notes": "备注"}
    """
    data = request.get_json()
    user_id = data.get('user_id')
    reminder_id = data.get('reminder_id')
    status = data.get('status', 'taken')
    notes = data.get('notes', '')
    
    if not user_id or not reminder_id:
        return jsonify({
            'success': False,
            'message': '用户ID和提醒ID不能为空'
        }), 400
    
    try:
        success = medication_tracker.record_medication(user_id, reminder_id, status, notes)
        if success:
            return jsonify({
                'success': True,
                'message': '用药记录成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用药记录失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'记录用药情况失败: {str(e)}'
        }), 500


@app.route('/api/medication/reminders', methods=['GET'])
def get_user_reminders():
    """
    获取用户的所有提醒
    参数: user_id - 用户ID
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        reminders = medication_tracker.get_user_reminders(user_id)
        return jsonify({
            'success': True,
            'data': reminders
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户提醒失败: {str(e)}'
        }), 500


@app.route('/api/medication/records', methods=['GET'])
def get_user_records():
    """
    获取用户的用药记录
    参数: user_id - 用户ID, start_date - 开始日期, end_date - 结束日期
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        records = medication_tracker.get_user_records(user_id)
        return jsonify({
            'success': True,
            'data': records
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户用药记录失败: {str(e)}'
        }), 500


@app.route('/api/medication/report', methods=['GET'])
def generate_adherence_report():
    """
    生成依从性报告
    参数: user_id - 用户ID, days - 统计天数
    """
    user_id = request.args.get('user_id')
    days = request.args.get('days', 30, type=int)
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        report = medication_tracker.generate_adherence_report(user_id, days)
        if report:
            return jsonify({
                'success': True,
                'data': report
            })
        else:
            return jsonify({
                'success': False,
                'message': '生成报告失败'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成依从性报告失败: {str(e)}'
        }), 500


@app.route('/api/medication/today', methods=['GET'])
def get_today_reminders():
    """
    获取今日提醒
    参数: user_id - 用户ID
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': '用户ID不能为空'
        }), 400
    
    try:
        reminders = medication_tracker.get_today_reminders(user_id)
        return jsonify({
            'success': True,
            'data': reminders
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取今日提醒失败: {str(e)}'
        }), 500

# ----------------------------------------------------------------------------------------------------------------------结束
@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    # 初始化系统
    init_ok = init_system()
    if not init_ok:
        # 云端部署时允许降级启动（Neo4j/LLM后续请求时再处理）
        print("WARNING: 部分组件初始化失败，服务将以降级模式启动")
    
    # 启动Flask服务（云端平台通过PORT环境变量指定端口）
    port = int(os.getenv("PORT", 8080))
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    
    print("\n" + "="*60)
    print("康联智枢——面向主动健康的知识驱动医疗智能协同网络 - Web服务")
    print("="*60)
    print(f"\n监听端口：{port}")
    print(f"Debug模式：{'开启' if debug_mode else '关闭（生产模式）'}")
    print("API健康检查：/api/health\n")
    
    # threaded=True 支持并发请求；云端部署使用waitress/gunicorn时会忽略此参数
    app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)

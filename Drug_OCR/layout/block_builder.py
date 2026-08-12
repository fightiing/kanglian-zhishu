"""药品说明书版面块构建工具

@author: wsy
@date: 2026.01.07
@desc: 将YOLO检测结果转换为统一的版面块结构
"""

def build_blocks(results):
    """构建统一的版面块结构
    
    Args:
        results: YOLO检测结果列表，每个元素包含:
            - bbox: 边界框坐标[x1,y1,x2,y2]
            - label: 块类型标签
            - score: 置信度
            
    Returns:
        List[Dict]: 标准化的块结构列表，每个元素包含:
            - type: 块类型(title/text/table等)
            - bbox: 边界框坐标
            - cx/cy: 中心点坐标
            - w/h: 宽高
            - text: 文本内容(初始为None)
    """
    blocks = []

    for r in results:
        x1, y1, x2, y2 = r["bbox"]
        block = {
            "type": r["label"],      # title / text / table
            "bbox": [x1, y1, x2, y2],
            "cx": (x1 + x2) / 2,
            "cy": (y1 + y2) / 2,
            "w": x2 - x1,
            "h": y2 - y1,
            "text": None
        }
        blocks.append(block)

    return blocks
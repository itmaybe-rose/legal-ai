from database import get_db
from models import Major

def init_majors():
    # 连接数据库
    db = next(get_db())
    
    # 常见的本科专业列表
    common_majors = [
        '计算机科学与技术', '软件工程', '数据科学与大数据技术', '人工智能', 
        '网络工程', '信息安全', '物联网工程', '电子信息工程', '通信工程', '自动化', 
        '电气工程及其自动化', '机械工程', '土木工程', '建筑学', '环境工程', 
        '化学工程与工艺', '材料科学与工程', '生物工程', '食品科学与工程', 
        '临床医学', '口腔医学', '药学', '护理学', '中医学', 
        '经济学', '金融学', '国际经济与贸易', '会计学', '财务管理', '市场营销', 
        '工商管理', '人力资源管理', '行政管理', '公共事业管理', 
        '法学', '教育学', '学前教育', '小学教育', 
        '汉语言文学', '英语', '日语', 
        '新闻学', '广播电视学', '广告学', 
        '历史学', '哲学', '社会学', '心理学'
    ]
    
    print(f"准备添加 {len(common_majors)} 个专业...")
    
    # 插入专业数据
    count = 0
    for major_name in common_majors:
        try:
            # 检查是否已存在
            existing = db.query(Major).filter(Major.name == major_name).first()
            if not existing:
                major = Major(name=major_name)
                db.add(major)
                db.commit()
                count += 1
                print(f"已添加专业: {major_name}")
            else:
                print(f"专业已存在: {major_name}")
        except Exception as e:
            print(f"添加专业 {major_name} 时出错: {e}")
            db.rollback()
    
    # 统计总数
    total = db.query(Major).count()
    print(f"\n初始化完成！")
    print(f"成功添加: {count} 个专业")
    print(f"现有专业总数: {total} 个")

if __name__ == "__main__":
    init_majors()
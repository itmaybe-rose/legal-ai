"""生活服务相关 API"""
from fastapi import APIRouter, Form
from utils.response import success

router = APIRouter()


@router.post("/api/life/heating_plan")
def get_heating_plan(
    district: str = Form(...),
    housing_type: str = Form(...),
    area: float = Form(...),
    duration: int = Form(...),
    is_commercial: bool = Form(...)
):
    """获取供暖方案"""
    # 根据地区、房屋类型等计算供暖费用
    # 这里使用简单的估算公式
    
    # 基础单价（元/平米/天）
    base_price = 0.2 if is_commercial else 0.15
    
    # 地区系数
    district_coefficient = {
        "东城区": 1.2,
        "西城区": 1.2,
        "海淀区": 1.1,
        "朝阳区": 1.1,
    }.get(district, 1.0)
    
    # 房屋类型系数
    housing_coefficient = {
        "住宅": 1.0,
        "公寓": 1.1,
        "别墅": 1.5,
    }.get(housing_type, 1.0)
    
    # 计算总费用
    total_cost = base_price * area * duration * district_coefficient * housing_coefficient
    
    return success(data={
        "district": district,
        "housing_type": housing_type,
        "area": area,
        "duration": duration,
        "estimated_cost": round(total_cost, 2),
        "daily_cost": round(total_cost / duration, 2),
        "unit_price": round(base_price * district_coefficient * housing_coefficient, 3)
    })

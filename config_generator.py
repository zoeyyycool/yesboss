#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss直聘配置生成器
支持简洁的输入方式，自动生成配置文件
"""

import json
import os
from typing import List, Dict, Any, Optional

class ConfigGenerator:
    def __init__(self):
        # 城市映射表
        self.cities = {
            "全国": "100010000",
            "北京": "101010100", 
            "上海": "101020100",
            "广州": "101280100",
            "深圳": "101280600",
            "杭州": "101210100",
            "成都": "101270100",
            "武汉": "101200100",
            "西安": "101110100",
            "南京": "101190100",
            "苏州": "101190400",
            "天津": "101030100",
            "重庆": "101040100",
            "长沙": "101250100",
            "郑州": "101180100",
            "济南": "101120100",
            "青岛": "101120200",
            "大连": "101070200",
            "厦门": "101230200",
            "福州": "101230100",
            "合肥": "101220100"
        }
        
        # 薪资映射表
        self.salaries = {
            "3k以下": "100",
            "3-5k": "101",
            "5-10k": "404",
            "10-20k": "405",
            "20-50k": "406",
            "50k以上": "407"
        }
        
        # 经验映射表
        self.experiences = {
            "不限": None,
            "1年内": "103",
            "1-3年": "104", 
            "3-5年": "105",
            "5-10年": "106",
            "10年以上": "109"
        }
        
        # 学历映射表
        self.degrees = {
            "不限": None,
            "大专": "202",
            "本科": "203",
            "硕士": "204"
        }
        
        # 公司规模映射表
        self.scales = {
            "不限": None,
            "0-20人": "301",
            "20-99人": "302", 
            "100-499人": "303",
            "500-999人": "304",
            "1000-9999人": "305",
            "10000人以上": "306"
        }

    def normalize_key(self, key: str) -> str:
        """标准化输入的键值"""
        return key.lower().replace("k", "k").replace("K", "k")

    def find_city_code(self, city_name: str) -> Optional[str]:
        """查找城市代码"""
        for city, code in self.cities.items():
            if city_name in city or city in city_name:
                return code
        return None

    def find_salary_code(self, salary_str: str) -> Optional[str]:
        """查找薪资代码"""
        salary_normalized = self.normalize_key(salary_str)
        for salary, code in self.salaries.items():
            if salary_normalized == salary or salary in salary_normalized:
                return code
        return None

    def find_experience_code(self, exp_str: str) -> Optional[str]:
        """查找经验代码"""
        for exp, code in self.experiences.items():
            if exp_str in exp or exp in exp_str:
                return code
        return None

    def find_degree_code(self, degree_str: str) -> Optional[str]:
        """查找学历代码"""
        for degree, code in self.degrees.items():
            if degree_str in degree or degree in degree_str:
                return code
        return None

    def find_scale_code(self, scale_str: str) -> Optional[str]:
        """查找公司规模代码"""
        for scale, code in self.scales.items():
            if scale_str in scale or scale in scale_str:
                return code
        return None

    def create_task(self, 
                   name: str,
                   query: str, 
                   city: str,
                   salary: str = None,
                   experience: str = None,
                   degree: str = None,
                   scale: str = None,
                   output_file: str = None) -> Dict[str, Any]:
        """创建单个搜索任务"""
        
        # 查找城市代码
        city_code = self.find_city_code(city)
        if not city_code:
            raise ValueError(f"未找到城市 '{city}' 的代码")
        
        # 查找薪资代码
        salary_code = None
        if salary:
            salary_code = self.find_salary_code(salary)
            if not salary_code:
                print(f"警告: 未找到薪资 '{salary}' 的代码，将设为不限")
        
        # 查找经验代码
        experience_code = None
        if experience:
            experience_code = self.find_experience_code(experience)
            if experience_code is None and experience != "不限":
                print(f"警告: 未找到经验 '{experience}' 的代码，将设为不限")
        
        # 查找学历代码
        degree_code = None
        if degree:
            degree_code = self.find_degree_code(degree)
            if degree_code is None and degree != "不限":
                print(f"警告: 未找到学历 '{degree}' 的代码，将设为不限")
        
        # 查找公司规模代码
        scale_code = None
        if scale:
            scale_code = self.find_scale_code(scale)
            if scale_code is None and scale != "不限":
                print(f"警告: 未找到公司规模 '{scale}' 的代码，将设为不限")
        
        # 生成输出文件名
        if not output_file:
            safe_name = name.replace(" ", "_").replace("/", "_")
            output_file = f"jobs_{safe_name}.json"
        
        task = {
            "name": name,
            "query": query,
            "city": city_code,
            "output_file": output_file
        }
        
        # 只添加有值的可选字段（符合URL参数规则）
        if salary_code:
            task["salary"] = salary_code
        if experience_code:
            task["experience"] = experience_code
        if degree_code:
            task["degree"] = degree_code
        if scale_code:
            task["scale"] = scale_code
            
        return task

    def generate_config(self, 
                       tasks: List[Dict[str, str]],
                       scroll_n: int = 8,
                       output_format: str = "json",
                       merge_results: bool = False,
                       merge_file: str = "all_jobs_merged.json") -> Dict[str, Any]:
        """生成完整的配置文件"""
        
        config_tasks = []
        for task_info in tasks:
            try:
                task = self.create_task(**task_info)
                config_tasks.append(task)
                print(f"✓ 已添加任务: {task['name']}")
            except Exception as e:
                print(f"✗ 任务创建失败: {e}")
        
        config = {
            "说明": "批量搜索配置文件 - 由配置生成器自动生成",
            "tasks": config_tasks,
            "global_settings": {
                "scroll_n": scroll_n,
                "filter_tags": [],
                "blacklist": [],
                "output_format": output_format,
                "merge_all_results": merge_results,
                "merge_output_file": merge_file
            }
        }
        
        return config

    def save_config(self, config: Dict[str, Any], filename: str = "batch_config.json"):
        """保存配置文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✓ 配置文件已保存: {filename}")

    def show_available_options(self):
        """显示可用的选项"""
        print("\n=== 可用选项参考 ===")
        
        print("\n城市选项:")
        cities_list = list(self.cities.keys())
        for i in range(0, len(cities_list), 4):
            print("  " + " | ".join(cities_list[i:i+4]))
        
        print("\n薪资选项:")
        salaries_list = list(self.salaries.keys())
        for i in range(0, len(salaries_list), 4):
            print("  " + " | ".join(salaries_list[i:i+4]))
        
        print("\n经验选项:")
        print("  " + " | ".join(self.experiences.keys()))
        
        print("\n学历选项:")
        print("  " + " | ".join(self.degrees.keys()))
        
        print("\n公司规模选项:")
        print("  " + " | ".join(self.scales.keys()))


def interactive_mode():
    """交互式配置生成"""
    generator = ConfigGenerator()
    
    print("=== Boss直聘配置生成器 ===")
    print("支持简洁输入，自动生成配置文件\n")
    
    # 显示可用选项
    show_options = input("是否显示可用选项? (y/n): ").lower().strip()
    if show_options == 'y':
        generator.show_available_options()
    
    tasks = []
    
    print("\n开始添加搜索任务 (输入空行结束):")
    
    while True:
        print(f"\n--- 任务 {len(tasks) + 1} ---")
        
        name = input("任务名称: ").strip()
        if not name:
            break
            
        query = input("搜索关键词: ").strip()
        if not query:
            print("搜索关键词不能为空")
            continue
            
        city = input("城市 (如: 北京, 上海): ").strip()
        if not city:
            print("城市不能为空")
            continue
        
        salary = input("薪资范围 (如: 10-20k, 可选): ").strip() or None
        experience = input("工作经验 (如: 3-5年, 可选): ").strip() or None
        degree = input("学历要求 (如: 本科, 可选): ").strip() or None
        scale = input("公司规模 (如: 100-499人, 可选): ").strip() or None
        output_file = input("输出文件名 (可选, 自动生成): ").strip() or None
        
        task_info = {
            "name": name,
            "query": query,
            "city": city,
            "salary": salary,
            "experience": experience,
            "degree": degree,
            "scale": scale,
            "output_file": output_file
        }
        
        tasks.append(task_info)
        print(f"✓ 任务 '{name}' 已添加")
    
    if not tasks:
        print("未添加任何任务，退出")
        return
    
    # 全局设置
    print("\n--- 全局设置 ---")
    scroll_n = input("滚动次数 (默认8): ").strip()
    scroll_n = int(scroll_n) if scroll_n.isdigit() else 8
    
    output_format = input("输出格式 (json/csv/txt, 默认json): ").strip().lower()
    if output_format not in ['json', 'csv', 'txt']:
        output_format = 'json'
    
    merge_results = input("是否合并所有结果? (y/n): ").lower().strip() == 'y'
    merge_file = "all_jobs_merged.json"
    if merge_results:
        merge_file = input("合并文件名 (默认all_jobs_merged.json): ").strip() or merge_file
    
    # 生成配置
    print("\n--- 生成配置 ---")
    config = generator.generate_config(
        tasks=tasks,
        scroll_n=scroll_n,
        output_format=output_format,
        merge_results=merge_results,
        merge_file=merge_file
    )
    
    # 保存配置
    filename = input("配置文件名 (默认batch_config.json): ").strip() or "batch_config.json"
    generator.save_config(config, filename)
    
    print(f"\n✓ 配置生成完成! 共 {len(config['tasks'])} 个任务")
    print(f"运行命令: python3 batch_search.py")


def quick_mode():
    """快速模式示例"""
    generator = ConfigGenerator()
    
    # 示例任务
    tasks = [
        {
            "name": "北京Python开发",
            "query": "Python开发",
            "city": "北京",
            "salary": "20-30k",
            "experience": "3-5年",
            "degree": "本科"
        },
        {
            "name": "上海产品经理",
            "query": "产品经理",
            "city": "上海",
            "salary": "15-20k",
            "experience": "3-5年"
        },
        {
            "name": "深圳前端开发",
            "query": "前端开发",
            "city": "深圳",
            "salary": "15-20k"
        }
    ]
    
    config = generator.generate_config(tasks, merge_results=True)
    generator.save_config(config, "example_config.json")
    
    print("✓ 示例配置已生成: example_config.json")


if __name__ == "__main__":
    print("选择模式:")
    print("1. 交互式配置")
    print("2. 查看示例")
    print("3. 显示可用选项")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == "1":
        interactive_mode()
    elif choice == "2":
        quick_mode()
    elif choice == "3":
        generator = ConfigGenerator()
        generator.show_available_options()
    else:
        print("无效选择")
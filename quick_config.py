#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss直聘快速配置生成器
支持一行命令生成配置文件

使用示例:
python3 quick_config.py "Python开发@北京,20-30k,3-5年,本科" "产品经理@上海,15-20k"

格式: "职位@城市,薪资,经验,学历"
其中薪资、经验、学历为可选参数
"""

import sys
import json
from config_generator import ConfigGenerator

def parse_task_string(task_str: str) -> dict:
    """解析任务字符串
    
    格式: "职位@城市,薪资,经验,学历,规模"
    示例: "Python开发@北京,10-20k,3-5年,本科,1000-9999人"
    """
    if '@' not in task_str:
        raise ValueError(f"任务格式错误: {task_str}，应为 '职位@城市,薪资,经验,学历,规模'")
    
    # 分离职位和其他参数
    query_part, params_part = task_str.split('@', 1)
    query = query_part.strip()
    
    # 分离城市和其他参数
    params = params_part.split(',')
    city = params[0].strip()
    
    # 解析可选参数
    salary = params[1].strip() if len(params) > 1 and params[1].strip() else None
    experience = params[2].strip() if len(params) > 2 and params[2].strip() else None
    degree = params[3].strip() if len(params) > 3 and params[3].strip() else None
    scale = params[4].strip() if len(params) > 4 and params[4].strip() else None
    
    # 生成任务名称
    name = f"{city}{query}"
    
    return {
        "name": name,
        "query": query,
        "city": city,
        "salary": salary,
        "experience": experience,
        "degree": degree,
        "scale": scale
    }

def main():
    if len(sys.argv) < 2:
        print("Boss直聘快速配置生成器")
        print("\n使用方法:")
        print("python3 quick_config.py \"职位@城市,薪资,经验,学历,规模\" [更多任务...]")
        print("\n示例:")
        print('python3 quick_config.py "Python开发@北京,10-20k,3-5年,本科,1000-9999人" "产品经理@上海,20-50k"')
        print("\n格式说明:")
        print("- 职位和城市是必需的，用@分隔")
        print("- 薪资、经验、学历、规模是可选的，用逗号分隔")
        print("- 可以添加多个任务，每个任务用引号包围")
        print("\n支持的参数:")
        
        generator = ConfigGenerator()
        generator.show_available_options()
        return
    
    generator = ConfigGenerator()
    tasks = []
    
    # 解析所有任务
    for i, task_str in enumerate(sys.argv[1:], 1):
        try:
            task_info = parse_task_string(task_str)
            tasks.append(task_info)
            print(f"✓ 任务 {i}: {task_info['name']}")
        except Exception as e:
            print(f"✗ 任务 {i} 解析失败: {e}")
            print(f"  输入: {task_str}")
    
    if not tasks:
        print("没有有效的任务，退出")
        return
    
    # 生成配置
    print(f"\n生成配置文件，共 {len(tasks)} 个任务...")
    config = generator.generate_config(tasks)
    
    # 保存配置
    generator.save_config(config)
    print(f"\n✓ 配置生成完成!")
    print("运行搜索: python3 batch_search.py")

if __name__ == "__main__":
    main()
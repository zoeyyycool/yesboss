#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss直聘配置模板生成器
提供常用的搜索模板，快速生成配置
"""

from config_generator import ConfigGenerator

class TemplateGenerator:
    def __init__(self):
        self.generator = ConfigGenerator()
        
        # 预定义模板
        self.templates = {
            "python_dev": {
                "name": "Python开发工程师搜索",
                "description": "搜索Python开发相关职位",
                "tasks": [
                    {"query": "Python开发", "salary": "15-20k", "experience": "3-5年", "degree": "本科"},
                    {"query": "Python后端", "salary": "20-30k", "experience": "3-5年", "degree": "本科"},
                    {"query": "Django开发", "salary": "15-20k", "experience": "1-3年", "degree": "本科"},
                    {"query": "Flask开发", "salary": "15-20k", "experience": "1-3年", "degree": "本科"}
                ]
            },
            
            "frontend_dev": {
                "name": "前端开发工程师搜索",
                "description": "搜索前端开发相关职位",
                "tasks": [
                    {"query": "前端开发", "salary": "15-20k", "experience": "3-5年", "degree": "本科"},
                    {"query": "Vue开发", "salary": "15-20k", "experience": "1-3年", "degree": "本科"},
                    {"query": "React开发", "salary": "20-30k", "experience": "3-5年", "degree": "本科"},
                    {"query": "JavaScript开发", "salary": "15-20k", "experience": "1-3年", "degree": "本科"}
                ]
            },
            
            "product_manager": {
                "name": "产品经理搜索",
                "description": "搜索产品经理相关职位",
                "tasks": [
                    {"query": "产品经理", "salary": "20-30k", "experience": "3-5年", "degree": "本科"},
                    {"query": "产品运营", "salary": "15-20k", "experience": "1-3年", "degree": "本科"},
                    {"query": "产品专员", "salary": "10-15k", "experience": "1-3年", "degree": "本科"},
                    {"query": "AI产品经理", "salary": "30-50k", "experience": "3-5年", "degree": "本科"}
                ]
            },
            
            "data_analyst": {
                "name": "数据分析师搜索",
                "description": "搜索数据分析相关职位",
                "tasks": [
                    {"query": "数据分析师", "salary": "15-20k", "experience": "1-3年", "degree": "本科"},
                    {"query": "数据科学家", "salary": "30-50k", "experience": "3-5年", "degree": "硕士"},
                    {"query": "算法工程师", "salary": "30-50k", "experience": "3-5年", "degree": "硕士"},
                    {"query": "机器学习", "salary": "30-50k", "experience": "3-5年", "degree": "硕士"}
                ]
            },
            
            "ui_designer": {
                "name": "UI设计师搜索",
                "description": "搜索UI/UX设计相关职位",
                "tasks": [
                    {"query": "UI设计师", "salary": "15-20k", "experience": "1-3年", "degree": "本科"},
                    {"query": "UX设计师", "salary": "20-30k", "experience": "3-5年", "degree": "本科"},
                    {"query": "交互设计师", "salary": "20-30k", "experience": "3-5年", "degree": "本科"},
                    {"query": "视觉设计师", "salary": "15-20k", "experience": "1-3年", "degree": "本科"}
                ]
            },
            
            "multi_city": {
                "name": "多城市搜索模板",
                "description": "在多个城市搜索同一职位",
                "cities": ["北京", "上海", "深圳", "杭州", "成都"],
                "tasks": [
                    {"query": "Python开发", "salary": "20-30k", "experience": "3-5年", "degree": "本科"}
                ]
            }
        }

    def show_templates(self):
        """显示所有可用模板"""
        print("=== 可用模板 ===\n")
        for key, template in self.templates.items():
            print(f"{key}: {template['name']}")
            print(f"   描述: {template['description']}")
            if 'cities' in template:
                print(f"   城市: {', '.join(template['cities'])}")
            print(f"   任务数: {len(template['tasks'])}")
            print()

    def generate_from_template(self, template_key: str, cities: list = None, 
                             custom_settings: dict = None) -> dict:
        """从模板生成配置"""
        if template_key not in self.templates:
            raise ValueError(f"模板 '{template_key}' 不存在")
        
        template = self.templates[template_key]
        tasks = []
        
        # 处理多城市模板
        if template_key == "multi_city":
            cities = cities or template['cities']
            for city in cities:
                for task_template in template['tasks']:
                    task_info = task_template.copy()
                    task_info['city'] = city
                    task_info['name'] = f"{city}{task_info['query']}"
                    tasks.append(task_info)
        else:
            # 处理普通模板
            cities = cities or ["北京"]  # 默认城市
            for city in cities:
                for task_template in template['tasks']:
                    task_info = task_template.copy()
                    task_info['city'] = city
                    task_info['name'] = f"{city}{task_info['query']}"
                    tasks.append(task_info)
        
        # 应用自定义设置
        settings = {
            "scroll_n": 8,
            "output_format": "json",
            "merge_results": False,
            "merge_file": "all_jobs_merged.json"
        }
        if custom_settings:
            settings.update(custom_settings)
        
        config = self.generator.generate_config(
            tasks=tasks,
            scroll_n=settings['scroll_n'],
            output_format=settings['output_format'],
            merge_results=settings['merge_results'],
            merge_file=settings['merge_file']
        )
        
        return config

def interactive_template_mode():
    """交互式模板选择"""
    generator = TemplateGenerator()
    
    print("=== Boss直聘模板配置生成器 ===\n")
    
    # 显示模板
    generator.show_templates()
    
    # 选择模板
    template_key = input("请选择模板 (输入模板key): ").strip()
    if template_key not in generator.templates:
        print("模板不存在")
        return
    
    # 选择城市
    print("\n选择城市 (多个城市用逗号分隔, 如: 北京,上海,深圳):")
    cities_input = input("城市 (默认北京): ").strip()
    if cities_input:
        cities = [city.strip() for city in cities_input.split(',')]
    else:
        cities = ["北京"]
    
    # 自定义设置
    print("\n--- 可选设置 ---")
    scroll_n = input("滚动次数 (默认8): ").strip()
    scroll_n = int(scroll_n) if scroll_n.isdigit() else 8
    
    merge_results = input("是否合并结果? (y/n): ").lower().strip() == 'y'
    
    custom_settings = {
        "scroll_n": scroll_n,
        "merge_results": merge_results
    }
    
    # 生成配置
    print(f"\n使用模板 '{template_key}' 生成配置...")
    config = generator.generate_from_template(template_key, cities, custom_settings)
    
    # 保存配置
    filename = input("配置文件名 (默认batch_config.json): ").strip() or "batch_config.json"
    generator.generator.save_config(config, filename)
    
    print(f"\n✓ 配置生成完成! 共 {len(config['tasks'])} 个任务")
    print(f"运行命令: python3 batch_search.py")

def quick_template_generate(template_key: str, cities: list = None):
    """快速生成模板配置"""
    generator = TemplateGenerator()
    
    try:
        config = generator.generate_from_template(template_key, cities)
        generator.generator.save_config(config)
        print(f"✓ 使用模板 '{template_key}' 生成配置完成!")
        print(f"✓ 共 {len(config['tasks'])} 个任务")
        print("运行命令: python3 batch_search.py")
    except Exception as e:
        print(f"✗ 生成失败: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # 交互模式
        interactive_template_mode()
    elif len(sys.argv) >= 2:
        # 命令行模式
        template_key = sys.argv[1]
        cities = sys.argv[2].split(',') if len(sys.argv) > 2 else None
        quick_template_generate(template_key, cities)
    else:
        print("使用方法:")
        print("python3 template_config.py                    # 交互模式")
        print("python3 template_config.py python_dev         # 使用模板")
        print("python3 template_config.py python_dev 北京,上海 # 指定城市")
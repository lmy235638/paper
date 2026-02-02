import yaml
import json


def load_config(config_path):
    """
    加载YAML配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_tasks(tasks_path):
    """
    加载任务数据
    
    Args:
        tasks_path: 任务数据文件路径
        
    Returns:
        任务列表
    """
    with open(tasks_path, 'r', encoding='utf-8') as f:
        return json.load(f)

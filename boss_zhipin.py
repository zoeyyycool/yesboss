"""
Boss直聘爬虫工具
功能：自动登录、搜索职位、提取职位信息并保存到本地文件
"""

# ==================== 导入必要的库 ====================
import re          # 正则表达式，用于匹配文本模式
import json        # JSON数据处理，用于保存和读取数据
import csv         # CSV文件处理，用于保存Excel可读的格式
import random      # 随机数生成，用于模拟人类操作（随机延迟）
from pathlib import Path  # 路径处理，用于操作文件路径
from typing import Callable, Optional, Union, Set, List  # 类型提示，帮助理解函数参数类型
from urllib.parse import urlencode, quote  # URL编码，用于构建搜索链接
from typing import AsyncGenerator  # 异步生成器类型
from playwright.async_api import BrowserContext, Page, Locator, async_playwright, expect  # 浏览器自动化工具
from pydantic import BaseModel  # 数据验证，确保数据格式正确


# ==================== 全局常量 ====================
# Boss直聘网站的基础URL
base_url = "https://www.zhipin.com"

# 城市代码到城市名称的映射表
city_code_mapping = {
    "100010000": "全国",
    "101010100": "北京",
    "101020100": "上海",
    "101280100": "广州",
    "101280600": "深圳",
    "101210100": "杭州",
    "101270100": "成都",
    "101200100": "武汉",
    "101110100": "西安",
    "101190100": "南京",
    "101190400": "苏州",
    "101030100": "天津",
    "101040100": "重庆",
    "101250100": "长沙",
    "101180100": "郑州",
    "101120100": "济南",
    "101120200": "青岛",
    "101070200": "大连",
    "101230200": "厦门",
    "101230100": "福州",
    "101220100": "合肥"
}

# 筛选项代码到可见文本的映射（用于在页面上点击筛选）
salary_code_to_text = {
    "101": "5K-10K",
    "102": "10K以下",
    "103": "10K-15K",
    "104": "15K-20K",
    "105": "20K-30K",
    "106": "30K-50K",
    "107": "50K以上",
}

experience_code_to_text = {
    "102": "应届生",
    "103": "在校/实习",
    "104": "1年以内",
    "106": "1-3年",
    "107": "3-5年",
    "108": "5-10年",
    "109": "10年以上",
}

degree_code_to_text = {
    "203": "大专",
    "204": "不限",
    "205": "本科",
    "206": "硕士",
    "207": "博士",
}

# 薪资字符映射表
# Boss直聘为了反爬虫，会用特殊字符显示数字，这个字典用于将特殊字符转换回正常数字
# 例如：chr(0xE031) 这个特殊字符代表数字 "0"
salary_mapping = {
    chr(0xE031): "0",  # 特殊字符 → 数字0
    chr(0xE032): "1",  # 特殊字符 → 数字1
    chr(0xE033): "2",  # 特殊字符 → 数字2
    chr(0xE034): "3",  # 特殊字符 → 数字3
    chr(0xE035): "4",  # 特殊字符 → 数字4
    chr(0xE036): "5",  # 特殊字符 → 数字5
    chr(0xE037): "6",  # 特殊字符 → 数字6
    chr(0xE038): "7",  # 特殊字符 → 数字7
    chr(0xE039): "8",  # 特殊字符 → 数字8
    chr(0xE03a): "9",  # 特殊字符 → 数字9
}


# ==================== Cookie管理函数 ====================

async def load_cookies(context: BrowserContext, cookies_path: Path) -> None:
    """
    从文件中加载cookies到浏览器上下文
    
    什么是cookies？
    - cookies是网站用来记住你登录状态的小文件
    - 保存cookies后，下次访问网站就不需要重新登录了
    
    参数：
        context: 浏览器上下文（可以理解为浏览器的一个会话）
        cookies_path: cookies文件保存的路径
    """
    # 检查cookies文件是否存在
    if cookies_path.exists():
        # 打开文件并读取cookies数据
        with open(cookies_path, "r") as f:
            data = json.load(f)  # 从JSON文件读取数据
        # 将cookies添加到浏览器上下文，这样浏览器就"记住"了登录状态
        await context.add_cookies(data["cookies"])


async def dump_cookies(context: BrowserContext, cookies_path: Path) -> None:
    """
    将浏览器中的cookies保存到文件
    
    参数：
        context: 浏览器上下文
        cookies_path: cookies文件保存的路径
    """
    # 从浏览器获取当前的cookies
    cookies = await context.cookies()
    # 将cookies保存到文件
    with open(cookies_path, "w") as f:
        json.dump({"cookies": cookies}, f)  # 将cookies保存为JSON格式


# ==================== 登录函数 ====================

async def login(context: BrowserContext, page: Page, cookies_path: Path, headless_cb: Optional[Callable[[str], None]] = None) -> bool:
    """
    登录Boss直聘网站
    
    登录流程：
    1. 先尝试加载之前保存的cookies（如果存在）
    2. 访问登录页面
    3. 检查是否已经登录（通过检查用户头像是否存在）
    4. 如果未登录，等待用户扫码登录
    5. 登录成功后保存cookies
    
    参数：
        context: 浏览器上下文
        page: 浏览器页面对象
        cookies_path: cookies文件路径
        headless_cb: 无头模式回调函数（用于获取二维码，一般不需要）
    
    返回：
        True: 登录成功
        False: 登录失败
    """
    # 步骤1: 尝试加载之前保存的cookies
    await load_cookies(context, cookies_path)
    
    # 步骤2: 访问登录页面
    # wait_until="networkidle" 表示等待页面完全加载完成
    await page.goto(f"{base_url}/web/user/?ka=header-login", wait_until="networkidle")
    
    # 步骤3: 查找用户头像元素（如果存在说明已经登录）
    figure = page.locator(".nav-figure")  # .nav-figure 是用户头像的CSS选择器
    
    # 步骤4: 循环检查登录状态（最多检查300次，每次等待1秒）
    for _ in range(300):
        # 如果用户头像可见，说明已经登录
        if await figure.is_visible():
            # 保存cookies，下次就不需要重新登录了
            await dump_cookies(context, cookies_path)
            return True  # 登录成功
        
        # 如果还没登录，尝试处理登录流程
        try:
            # 如果是无头模式（后台运行），需要处理二维码
            if headless_cb:
                wx_btn = page.locator(".wx-login-btn")  # 微信登录按钮
                if await wx_btn.is_visible():
                    # 点击微信登录按钮
                    await wx_btn.click(delay=random.randint(32, 512))  # 随机延迟，模拟人类操作
                    # 获取二维码
                    qrcode = page.locator(".mini-qrcode")
                    await expect(qrcode).to_be_visible()  # 等待二维码出现
                    # 调用回调函数，传递二维码图片地址
                    headless_cb(await qrcode.get_attribute("src"))
            
            # 等待用户头像出现（等待1秒）
            await expect(figure).to_be_visible(timeout=1000)
        except AssertionError:
            # 如果等待超时，继续循环检查
            pass
    
    # 如果300次循环后还没登录，返回False
    return False


# ==================== 薪资解码函数 ====================

def decode_salary(salary: str) -> str:
    """
    将Boss直聘的特殊字符薪资转换为正常数字
    
    为什么需要这个函数？
    - Boss直聘为了反爬虫，会用特殊字符显示薪资数字
    - 例如："20-30K" 可能显示为特殊字符，需要转换回正常数字
    
    参数：
        salary: 包含特殊字符的薪资字符串
    
    返回：
        转换后的正常薪资字符串
    
    示例：
        输入: "2" + 特殊字符 + "0-3" + 特殊字符 + "0K"
        输出: "20-30K"
    """
    # 遍历薪资字符串中的每个字符
    # 如果字符在映射表中，替换为对应的数字；否则保持原样
    return "".join(salary_mapping[c] if c in salary_mapping else c for c in salary)


# ==================== Job类：表示一个职位 ====================

class Job:
    """
    职位类，用于存储和操作职位信息
    
    包含的信息：
    - company: 公司名称
    - title: 职位名称
    - salary: 薪资范围
    - experience: 工作年限要求
    - desc: 职位描述
    - url: 职位详情链接（完整URL）
    - city: 工作城市
    """
    
    class Info(BaseModel):
        """
        职位信息数据模型（使用Pydantic进行数据验证）
        
        什么是BaseModel？
        - 这是Pydantic库提供的功能，用于确保数据格式正确
        - 如果数据格式不对，会自动报错
        """
        company: str  # 公司名称
        title: str    # 职位名称
        salary: str   # 薪资范围
        experience: str  # 工作年限要求
        desc: str     # 职位描述
        url: str      # 职位详情链接（完整URL）
        city: str     # 工作城市

        def description(self) -> str:
            """
            将职位信息格式化为字符串
            
            返回：
                格式化的职位描述字符串
            """
            return f"<company>{self.company}</company>\n<title>{self.title}</title>\n<salary>{self.salary}</salary>\n<experience>{self.experience}</experience>\n<city>{self.city}</city>\n<description>\n{self.desc}\n</description>"

    # 职位信息对象
    _info: Info

    def __init__(self, info: Info):
        """
        初始化职位对象
        
        参数：
            info: 职位信息对象
        """
        self._info = info

    def description(self) -> str:
        """
        获取格式化的职位描述
        
        返回：
            格式化的职位描述字符串
        """
        return self._info.description()

    def model_dump(self) -> dict[str, str]:
        """
        将职位信息转换为字典格式
        
        为什么需要这个方法？
        - 字典格式便于保存到JSON文件
        - 也便于在代码中操作数据
        
        返回：
            包含职位信息的字典
        """
        return self._info.model_dump()


# ==================== BossZhipin类：主要的爬虫类 ====================

class BossZhipin:
    """
    Boss直聘爬虫主类
    
    功能：
    1. 管理登录状态（通过cookies）
    2. 搜索职位
    3. 提取职位信息
    4. 保存职位信息到本地文件
    """
    
    # cookies文件路径
    _cookies_path: Path

    def __init__(self, cookies_path: str = "cookies.json", headless_cb: Optional[Callable[[str], None]] = None):
        """
        初始化BossZhipin对象
        
        参数：
            cookies_path: cookies文件路径（默认"cookies.json"）
            headless_cb: 无头模式回调函数（一般不需要）
        """
        # 将字符串路径转换为Path对象，并解析为绝对路径
        self._cookies_path = Path(cookies_path).resolve()
        # 保存无头模式回调函数
        self._headless_cb = headless_cb

    @staticmethod
    def load_config(config_path: str = "search_config.json") -> dict:
        """
        从配置文件加载搜索参数
        
        参数：
            config_path: 配置文件路径（默认"search_config.json"）
        
        返回：
            包含搜索参数的字典
        
        示例：
            config = BossZhipin.load_config("search_config.json")
            print(config["search_params"]["query"])
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        return config

    @staticmethod
    def save_jobs(jobs: Union[List[Job], List[dict]], output_file: str = "jobs_data.json", format: str = "json") -> None:
        """
        保存职位信息到本地文件
        
        支持三种格式：
        1. JSON格式：结构化数据，便于程序处理
        2. CSV格式：可以用Excel打开，便于查看和分析
        3. TXT格式：纯文本格式，可读性最好
        
        参数：
            jobs: Job对象列表或字典列表
            output_file: 输出文件名
            format: 文件格式，支持 'json', 'csv', 'txt'
        
        示例：
            # 保存为JSON格式
            BossZhipin.save_jobs(jobs_list, "jobs.json", format="json")
            
            # 保存为CSV格式（可以用Excel打开）
            BossZhipin.save_jobs(jobs_list, "jobs.csv", format="csv")
            
            # 保存为TXT格式（可读性最好）
            BossZhipin.save_jobs(jobs_list, "jobs.txt", format="txt")
        """
        # 检查是否有职位数据
        if not jobs:
            print("没有职位数据需要保存")
            return
        
        # 将字符串路径转换为Path对象
        output_path = Path(output_file)
        
        # 步骤1: 统一转换为字典列表
        # 如果输入是Job对象列表，转换为字典列表
        if isinstance(jobs[0], Job):
            jobs_data = [job.model_dump() for job in jobs]
        # 如果输入已经是字典列表，直接使用
        elif isinstance(jobs[0], dict):
            jobs_data = jobs
        else:
            # 如果格式不对，抛出错误
            raise ValueError("jobs 必须是 Job 对象列表或字典列表")
        
        # 步骤2: 根据格式保存文件
        if format.lower() == "json":
            # JSON格式：结构化数据，便于程序处理
            with open(output_path, "w", encoding="utf-8") as f:
                # ensure_ascii=False: 允许中文字符
                # indent=2: 缩进2个空格，让文件更易读
                json.dump(jobs_data, f, ensure_ascii=False, indent=2)
            print(f"✓ 已保存 {len(jobs_data)} 个职位到: {output_path} (JSON格式)")
            
        elif format.lower() == "csv":
            # CSV格式：可以用Excel打开
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                # 创建CSV写入器，指定列名（包含experience字段）
                writer = csv.DictWriter(f, fieldnames=["company", "title", "salary", "experience", "desc", "url", "city"])
                writer.writeheader()  # 写入表头
                # 逐行写入职位数据
                for job in jobs_data:
                    writer.writerow(job)
            print(f"✓ 已保存 {len(jobs_data)} 个职位到: {output_path} (CSV格式)")
            
        elif format.lower() == "txt":
            # TXT格式：可读性最好
            with open(output_path, "w", encoding="utf-8") as f:
                # 遍历每个职位，格式化写入
                for i, job in enumerate(jobs_data, 1):
                    f.write(f"{'='*60}\n")  # 分隔线
                    f.write(f"职位 #{i}\n")  # 职位编号
                    f.write(f"{'='*60}\n")
                    f.write(f"公司: {job['company']}\n")
                    f.write(f"职位: {job['title']}\n")
                    f.write(f"薪资: {job['salary']}\n")
                    f.write(f"工作年限: {job.get('experience', '不限')}\n")
                    f.write(f"城市: {job.get('city', '未知')}\n")
                    f.write(f"链接: {job['url']}\n")
                    f.write(f"\n职位描述:\n{job['desc']}\n")
                    f.write(f"\n{'='*60}\n\n")
            print(f"✓ 已保存 {len(jobs_data)} 个职位到: {output_path} (TXT格式)")
            
        else:
            # 如果格式不支持，抛出错误
            raise ValueError(f"不支持的格式: {format}，支持 'json', 'csv', 'txt'")

    async def query_jobs(self, query: str, city: str, salary: Optional[str] = None, experience: Optional[str] = None, degree: Optional[str] = None, scroll_n: int = 8, filter_tags: Optional[Set[str]] = None, blacklist: Optional[Set[str]] = None) -> AsyncGenerator[Job, None]:
        """
        搜索职位并提取职位信息
        
        工作流程：
        1. 启动浏览器
        2. 登录（如果未登录）
        3. 访问搜索页面
        4. 滚动页面加载更多职位
        5. 遍历每个职位，提取信息
        6. 过滤不符合条件的职位
        7. 返回职位对象
        
        参数：
            query: 搜索关键词（例如："Python开发"）
            city: 城市代码（例如："100010000"表示北京）
            salary: 薪资范围（可选，例如："103"表示10K-15K）
            experience: 工作经验（可选，例如："106"表示1-3年）
            degree: 学历要求（可选，例如："205"表示本科）
            scroll_n: 滚动加载次数（默认8次，滚动越多加载的职位越多）
            filter_tags: 过滤标签（可选，例如：{"急招"}表示过滤掉"急招"标签的职位）
            blacklist: 公司黑名单（可选，例如：{"某公司"}表示过滤掉这个公司的职位）
        
        返回：
            职位对象的异步生成器（可以逐个获取职位）
        
        示例：
            async for job in boss.query_jobs("Python", "100010000"):
                print(job.model_dump())
        """
        # 从城市代码获取城市名称（作为默认值）
        default_city = city_code_mapping.get(city, "未知")
        # 步骤1: 启动浏览器
        async with async_playwright() as p:
            # 启动Chromium浏览器
            # headless: 是否无头模式（True=后台运行，False=显示浏览器窗口）
            # args: 浏览器参数，用于隐藏自动化标识
            browser = await p.chromium.launch(
                headless = True if self._headless_cb else False,
                args = ["--disable-blink-features=AutomationControlled"]  # 隐藏自动化标识
            )
            # 创建浏览器上下文（可以理解为浏览器的一个会话）
            context = await browser.new_context()
            # 创建新页面
            page = await context.new_page()
            
            # 步骤2: 登录（如果登录失败，直接返回）
            if not await login(context, page, self._cookies_path, self._headless_cb):
                return  # 登录失败，退出函数
            
            # 步骤3: 构建搜索URL并访问
            # 构建搜索参数（基础参数：关键词和城市）
            params = dict(query=query, city=city)
            # 如果指定了薪资范围，添加到参数中
            if salary:
                params["salary"] = salary
            # 如果指定了工作经验，添加到参数中
            if experience:
                params["experience"] = experience
            # 如果指定了学历要求，添加到参数中
            if degree:
                params["degree"] = degree
            # 访问搜索页面
            # urlencode: 将参数编码为URL格式
            await page.goto(f"{base_url}/web/geek/jobs?{urlencode(params, quote_via=quote)}")

            # 尝试在页面上应用筛选：薪资/经验/学历（有些筛选不会通过URL参数生效）
            try:
                # 可能的筛选区域容器选择器集合
                filter_containers = [
                    ".filter-wrapper",
                    ".search-condition-wrapper",
                    ".condition-box",
                    ".search-job-condition",
                ]
                filter_container: Optional[Locator] = None
                for sel in filter_containers:
                    c = page.locator(sel)
                    if await c.count() > 0 and await c.first.is_visible():
                        filter_container = c.first
                        break

                async def click_option(texts: list[str]) -> None:
                    if not filter_container:
                        return
                    for t in texts:
                        try:
                            opt = page.get_by_text(t, exact=True)
                            if await opt.count() > 0:
                                await opt.first.click()
                                # 等待内容刷新
                                await page.wait_for_timeout(300)
                                # 筛选后停留：模拟用户查看筛选结果（800-1500毫秒）
                                await page.wait_for_timeout(random.randint(800, 1500))
                                break
                        except:
                            continue

                # 薪资筛选
                if salary:
                    salary_text = salary_code_to_text.get(str(salary))
                    if salary_text:
                        await click_option([salary_text])

                # 经验筛选
                if experience:
                    exp_text = experience_code_to_text.get(str(experience))
                    if exp_text:
                        await click_option([exp_text])

                # 学历筛选
                if degree:
                    deg_text = degree_code_to_text.get(str(degree))
                    if deg_text:
                        await click_option([deg_text])
            except:
                # 忽略筛选点击失败，继续以页面显示为准
                pass
            
            # 步骤4: 滚动页面加载更多职位
            prev_h = 0  # 记录上一次的页面高度
            container = page.locator(".job-list-container")  # 职位列表容器
            await expect(container).to_be_visible()  # 等待容器出现
            await container.hover()  # 鼠标悬停在容器上
            
            # 初始停留：模拟用户查看页面（1-2秒）
            await page.wait_for_timeout(random.randint(1000, 2000))
            
            # 循环滚动scroll_n次
            for _ in range(scroll_n):
                # 获取容器的边界框（位置和大小）
                bbox = await container.bounding_box()
                # 向下滚动（滚动距离 = 当前高度 - 之前的高度）
                await page.mouse.wheel(0, bbox["height"] - prev_h)
                
                # 滚动后停留：模拟用户浏览职位列表（1.5-3秒）
                await page.wait_for_timeout(random.randint(1500, 3000))
                
                # 等待加载动画
                loading = container.locator(".loading-wait")
                try:
                    # 等待加载动画出现
                    await expect(loading).to_be_visible()
                    # 等待加载动画消失（表示加载完成）
                    await expect(loading).to_be_hidden()
                    
                    # 加载完成后短暂停留（500-1000毫秒）
                    await page.wait_for_timeout(random.randint(500, 1000))
                    
                    # 如果页面高度增加了，说明加载了新内容
                    if bbox["height"] > prev_h:
                        prev_h = bbox["height"]  # 更新之前的高度
                    else:
                        # 如果高度没变，说明没有更多内容了，退出循环
                        break
                except AssertionError:
                    # 如果加载动画没有出现，说明已经加载完所有内容，退出循环
                    break
            
            # 步骤5: 获取所有职位卡片
            jobs = await container.locator(".job-card-box").all()
            
            # 步骤6: 遍历每个职位，提取信息
            for job in jobs:
                # 步骤6.1: 过滤标签检查
                # 如果指定了过滤标签
                if filter_tags:
                    tag = job.locator(".job-tag-icon")  # 职位标签图标
                    # 如果标签可见且标签内容在过滤列表中，跳过这个职位
                    if await tag.is_visible() and await tag.get_attribute("alt") in filter_tags:
                        continue  # 跳过这个职位
                
                # 步骤6.2: 在点击之前先获取城市信息（更可靠）
                company = job.locator(".boss-name")  # 公司名称元素
                
                # 先尝试从职位卡片获取城市（在点击之前）
                job_city = default_city  # 使用搜索时的城市作为默认值
                try:
                    # 尝试多个选择器从职位卡片获取城市
                    for selector in [".job-area", ".job-limit", ".job-info .job-area", ".job-info .job-limit"]:
                        try:
                            area_elem = job.locator(selector)
                            if await area_elem.is_visible():
                                city_text = await area_elem.inner_text()
                                if city_text and city_text.strip():
                                    # 提取城市名称（可能包含区域，只取城市名）
                                    city_parts = city_text.strip().split()
                                    if city_parts:
                                        # 取第一个部分，通常是城市名
                                        job_city = city_parts[0]
                                        # 如果提取成功，跳出循环
                                        if job_city != "未知":
                                            break
                        except:
                            continue
                except:
                    pass
                
                # 点击前短暂停留：模拟用户思考（300-800毫秒）
                await page.wait_for_timeout(random.randint(300, 800))
                
                # 点击职位卡片，打开详情页（随机延迟，模拟人类操作）
                await job.click(delay=random.randint(32, 512))
                
                # 点击后等待：模拟页面切换时间（500-1000毫秒）
                await page.wait_for_timeout(random.randint(500, 1000))
                
                # 步骤6.3: 等待详情页加载并提取信息
                jd = page.locator(".job-detail-box")  # 职位详情框
                title = jd.locator(".job-name")        # 职位名称
                salary = jd.locator(".job-salary")     # 薪资
                desc = jd.locator(".desc")             # 职位描述
                boss = jd.locator(".job-boss-info")    # HR信息
                
                # 等待关键元素出现
                await expect(desc).to_be_visible()
                await expect(boss).to_be_visible()
                
                # 步骤6.4: 检查HR活跃时间
                # 如果HR活跃时间过长（周/月/年），说明HR可能不活跃，跳过这个职位
                active = boss.locator(".boss-active-time")
                if await active.is_visible() and re.search(r"[周月年]", await active.inner_text()):
                    continue  # 跳过这个职位
                
                # 步骤6.5: 提取公司名称
                company_name = await company.inner_text()
                
                # 步骤6.6: 提取工作城市（如果之前没获取到，从详情页获取）
                # 方法1: 如果之前从职位卡片获取失败，从职位详情页获取
                if job_city == default_city or job_city == "未知":
                    try:
                        # 尝试多个可能的选择器从详情页获取
                        for selector in [
                            ".job-location", 
                            ".job-area", 
                            ".location", 
                            ".job-info .location",
                            ".info-primary .location",
                            ".job-primary .location",
                            ".job-header .location",
                            ".job-detail-header .location"
                        ]:
                            try:
                                city_elem = jd.locator(selector)
                                if await city_elem.is_visible():
                                    city_text = await city_elem.inner_text()
                                    if city_text and city_text.strip():
                                        city_parts = city_text.strip().split()
                                        if city_parts:
                                            job_city = city_parts[0]
                                            # 如果提取成功且不是默认值，跳出循环
                                            if job_city != default_city and job_city != "未知":
                                                break
                            except:
                                continue
                    except:
                        pass
                
                # 方法2: 如果都获取不到，尝试从职位基本信息区域文本中提取
                if job_city == default_city or job_city == "未知":
                    try:
                        # 从职位基本信息区域获取
                        for info_selector in [".info-primary", ".job-primary", ".job-header", ".job-detail-header"]:
                            try:
                                info_elem = jd.locator(info_selector)
                                if await info_elem.is_visible():
                                    info_text = await info_elem.inner_text()
                                    # 尝试从文本中提取城市（常见城市名称）
                                    city_list = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "苏州", 
                                               "天津", "重庆", "长沙", "郑州", "济南", "青岛", "大连", "厦门", "福州", "合肥"]
                                    for c in city_list:
                                        if c in info_text:
                                            job_city = c
                                            break
                                    if job_city != default_city and job_city != "未知":
                                        break
                            except:
                                continue
                    except:
                        pass
                
                # 方法3: 如果还是获取不到，使用搜索时的城市作为默认值
                if job_city == "未知":
                    job_city = default_city
                
                # 步骤6.7: 获取职位链接并生成完整URL
                job_url_relative = await job.locator(".job-name").get_attribute("href")
                # 生成完整URL
                if job_url_relative:
                    if job_url_relative.startswith("http"):
                        job_url_full = job_url_relative  # 如果已经是完整URL
                    else:
                        job_url_full = f"{base_url}{job_url_relative}"  # 拼接完整URL
                else:
                    job_url_full = ""
                
                # 代码级关键词过滤（确保与搜索词相关）
                title_text = await title.inner_text()
                desc_text = await desc.inner_text()
                if query:
                    q = str(query).strip()
                    if q:
                        # 将搜索词按空格分割成多个关键词
                        keywords = [kw.strip() for kw in q.split() if kw.strip()]
                        
                        # 检查是否所有关键词都在标题或描述中出现
                        title_lower = title_text.lower()
                        desc_lower = desc_text.lower()
                        
                        # 如果有多个关键词，要求所有关键词都出现在标题或描述中
                        all_keywords_found = True
                        for keyword in keywords:
                            keyword_lower = keyword.lower()
                            if (keyword_lower not in title_lower) and (keyword_lower not in desc_lower):
                                all_keywords_found = False
                                break
                        
                        # 如果不是所有关键词都找到，跳过这个职位
                        if not all_keywords_found:
                            continue

                # 城市过滤：仅保留与搜索城市一致的职位
                if job_city != default_city:
                    continue

                # 猎头过滤：排除猎头公司发布的职位
                # 猎头公司名称通常包含"某"字，如"某大型互联网公司"、"某知名企业"等
                if "某" in company_name:
                    continue

                # 步骤6.8: 提取工作年限要求
                experience_text = "不限"  # 默认值
                try:
                    # 尝试从职位基本信息区域提取工作年限
                    for info_selector in [".info-primary", ".job-primary", ".job-header", ".job-detail-header"]:
                        try:
                            info_elem = jd.locator(info_selector)
                            if await info_elem.is_visible():
                                info_text = await info_elem.inner_text()
                                # 使用正则表达式匹配工作年限
                                experience_match = re.search(r'(\d+[-~]\d+年|\d+年以上|不限|应届|实习)', info_text)
                                if experience_match:
                                    experience_text = experience_match.group(1)
                                    break
                        except:
                            continue
                    
                    # 如果从基本信息区域没找到，尝试从职位描述中提取
                    if experience_text == "不限":
                        desc_lower = desc_text.lower()
                        # 匹配常见的工作年限表达
                        patterns = [
                            r'(\d+[-~]\d+年工作经验)',
                            r'(\d+年以上工作经验)',
                            r'(应届毕业生)',
                            r'(\d+[-~]\d+年经验)',
                            r'(\d+年以上经验)',
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, desc_text)
                            if match:
                                experience_text = match.group(1)
                                break
                except:
                    pass  # 如果提取失败，保持默认值

                # 步骤6.9: 黑名单检查
                # 如果指定了黑名单且公司在黑名单中，跳过这个职位
                if not blacklist or company_name not in blacklist:
                    # 详情页浏览停留：模拟用户阅读职位详情（2-5秒）
                    await page.wait_for_timeout(random.randint(2000, 5000))
                    
                    # 随机鼠标移动：模拟用户浏览行为
                    try:
                        # 获取页面尺寸
                        viewport = page.viewport_size
                        if viewport:
                            # 随机移动鼠标到页面中的某个位置
                            random_x = random.randint(100, viewport["width"] - 100)
                            random_y = random.randint(100, viewport["height"] - 100)
                            await page.mouse.move(random_x, random_y)
                            # 短暂停留（200-500毫秒）
                            await page.wait_for_timeout(random.randint(200, 500))
                    except:
                        pass  # 如果鼠标移动失败，忽略错误
                    
                    # 步骤6.10: 创建职位对象并返回
                    yield Job(Job.Info(
                        company = company_name,  # 公司名称
                        title = title_text,  # 职位名称
                        salary = decode_salary(await salary.inner_text()),  # 薪资（需要解码）
                        experience = experience_text,  # 工作年限要求
                        desc = desc_text,  # 职位描述
                        url = job_url_full,  # 职位链接（完整URL）
                        city = job_city,  # 工作城市
                    ))

    async def query_jobs_from_config(self, config_path: str = "search_config.json") -> AsyncGenerator[Job, None]:
        """
        从配置文件读取参数并搜索职位
        
        这个方法会自动读取配置文件，然后调用 query_jobs 方法进行搜索
        
        参数：
            config_path: 配置文件路径（默认"search_config.json"）
        
        返回：
            职位对象的异步生成器
        
        示例：
            async for job in boss.query_jobs_from_config("search_config.json"):
                print(job.model_dump())
        """
        # 加载配置文件
        config = self.load_config(config_path)
        
        # 提取搜索参数
        search_params = config.get("search_params", {})
        scroll_settings = config.get("scroll_settings", {})
        filter_settings = config.get("filter_settings", {})
        
        # 调用 query_jobs 方法进行搜索
        async for job in self.query_jobs(
            query=search_params.get("query", ""),
            city=search_params.get("city", ""),
            salary=search_params.get("salary"),
            experience=search_params.get("experience"),
            degree=search_params.get("degree"),
            scroll_n=scroll_settings.get("scroll_n", 8),
            filter_tags=set(filter_settings.get("filter_tags", [])) if filter_settings.get("filter_tags") else None,
            blacklist=set(filter_settings.get("blacklist", [])) if filter_settings.get("blacklist") else None
        ):
            yield job

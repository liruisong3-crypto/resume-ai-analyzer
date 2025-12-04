import os
import json
import tempfile
import uuid
import base64
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from .parser import PDFParser
from .ai_extractor import AIExtractor
from .matcher import ResumeMatcher
from .cache import CacheManager

# 初始化FastAPI应用
app = FastAPI(
    title="AI Resume Analyzer API",
    description="智能简历分析系统",
    version="1.0.0"
)

# 初始化组件
pdf_parser = PDFParser()
ai_extractor = AIExtractor()
resume_matcher = ResumeMatcher()
cache_manager = CacheManager()

# 临时存储（生产环境应用Redis）
resume_storage = {}

@app.get("/")
async def root():
    """根路径，返回服务状态"""
    return {
        "service": "AI Resume Analyzer API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "/api/upload (POST)",
            "analyze": "/api/analyze/{resume_id} (POST)",
            "get_resume": "/api/resume/{resume_id} (GET)"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": uuid.uuid4().hex}

@app.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    上传并解析简历PDF
    
    Args:
        file: PDF格式的简历文件
        
    Returns:
        JSON格式的解析结果
    """
    try:
        # 检查文件类型
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # 检查文件大小（限制10MB）
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置文件指针
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # 生成唯一ID
        resume_id = str(uuid.uuid4())
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 检查缓存
            cache_key = f"upload_{hash(content)}"
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                cached_result['resume_id'] = resume_id
                cached_result['from_cache'] = True
                resume_storage[resume_id] = cached_result
                return JSONResponse(content=cached_result)
            
            # 解析PDF
            text_content = pdf_parser.parse(tmp_file_path)
            
            # 提取关键信息
            extracted_info = ai_extractor.extract_info(text_content)
            
            # 存储结果
            result = {
                "resume_id": resume_id,
                "filename": file.filename,
                "file_size": file_size,
                "status": "success",
                "extracted_info": extracted_info,
                "text_preview": text_content[:500] + "..." if len(text_content) > 500 else text_content,
                "from_cache": False
            }
            
            resume_storage[resume_id] = result
            cache_manager.set(cache_key, result, ttl=3600)  # 缓存1小时
            
            return JSONResponse(content=result)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_file_path)
            except:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@app.post("/api/analyze/{resume_id}")
async def analyze_resume(
    resume_id: str,
    job_description: str = Form(...),
    use_ai_matching: bool = Form(True)
):
    """
    分析简历与岗位匹配度
    
    Args:
        resume_id: 简历ID
        job_description: 岗位描述
        use_ai_matching: 是否使用AI匹配
        
    Returns:
        匹配分析结果
    """
    try:
        # 获取简历数据
        if resume_id not in resume_storage:
            raise HTTPException(
                status_code=404,
                detail="Resume not found"
            )
        
        resume_data = resume_storage[resume_id]
        
        # 生成缓存键
        cache_key = f"analyze_{resume_id}_{hash(job_description)}_{use_ai_matching}"
        cached_result = cache_manager.get(cache_key)
        
        if cached_result:
            cached_result['from_cache'] = True
            return JSONResponse(content=cached_result)
        
        # 进行匹配分析
        match_result = resume_matcher.match(
            resume_data["extracted_info"],
            job_description,
            use_ai=use_ai_matching
        )
        
        result = {
            "resume_id": resume_id,
            "job_description_preview": job_description[:200] + "..." if len(job_description) > 200 else job_description,
            "match_result": match_result,
            "from_cache": False
        }
        
        cache_manager.set(cache_key, result, ttl=1800)  # 缓存30分钟
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/api/resume/{resume_id}")
async def get_resume(resume_id: str):
    """
    获取简历信息
    
    Args:
        resume_id: 简历ID
        
    Returns:
        简历信息
    """
    if resume_id in resume_storage:
        return JSONResponse(content={
            "status": "success",
            "resume_id": resume_id,
            "data": resume_storage[resume_id]
        })
    
    raise HTTPException(
        status_code=404,
        detail="Resume not found"
    )

# 阿里云函数计算适配器
def handler(event, context):
    """
    阿里云函数计算入口函数
    
    Args:
        event: 事件对象
        context: 上下文对象
        
    Returns:
        响应对象
    """
    from fastapi.middleware.wsgi import WSGIMiddleware
    from io import BytesIO
    import sys
    
    # 设置环境变量
    os.environ.update({
        'REDIS_HOST': os.getenv('REDIS_HOST', ''),
        'REDIS_PORT': os.getenv('REDIS_PORT', '6379'),
        'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD', '')
    })
    
    # 解析请求
    try:
        # 获取请求信息
        path = event.get('path', '/')
        http_method = event.get('httpMethod', 'GET').upper()
        headers = event.get('headers', {})
        query_params = event.get('queryParameters', {})
        body = event.get('body', '')
        
        # 处理base64编码的body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)
        
        # 构建ASGI scope
        scope = {
            'type': 'http',
            'method': http_method,
            'path': path,
            'query_string': '',
            'headers': [],
            'body': body.encode() if isinstance(body, str) else body
        }
        
        # 添加请求头
        for key, value in (headers or {}).items():
            scope['headers'].append((
                key.lower().encode(),
                str(value).encode()
            ))
        
        # 创建响应变量
        response_status = 200
        response_headers = []
        response_body = b''
        
        # 运行ASGI应用
        async def run_app():
            nonlocal response_status, response_headers, response_body
            
            async def receive():
                return {
                    'type': 'http.request',
                    'body': scope['body'],
                    'more_body': False
                }
            
            async def send(event):
                nonlocal response_status, response_headers, response_body
                if event['type'] == 'http.response.start':
                    response_status = event['status']
                    response_headers = event['headers']
                elif event['type'] == 'http.response.body':
                    response_body = event.get('body', b'')
        
            await app(scope, receive, send)
        
        # 运行事件循环
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_app())
        finally:
            loop.close()
        
        # 构建响应
        return {
            'isBase64Encoded': False,
            'statusCode': response_status,
            'headers': {k.decode(): v.decode() for k, v in response_headers},
            'body': response_body.decode('utf-8', errors='ignore')
        }
        
    except Exception as e:
        return {
            'isBase64Encoded': False,
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'detail': str(e)
            })
        }

# 本地运行
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
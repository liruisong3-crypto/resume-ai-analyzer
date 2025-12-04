import json
import time
from typing import Any, Optional
import os

class CacheManager:
    def __init__(self):
        self.cache_enabled = True
        self.memory_cache = {}
        self.cache_expiry = {}
        
        # 从环境变量获取 Redis 配置
        redis_host = os.getenv('REDIS_HOST', '')
        redis_port = os.getenv('REDIS_PORT', '6379')
        redis_password = os.getenv('REDIS_PASSWORD', '')
        
        # 如果配置了 Redis，尝试连接
        if redis_host:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=int(redis_port),
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3
                )
                # 测试连接
                self.redis_client.ping()
                print("[SUCCESS] Redis缓存已启用: {redis_host}:{redis_port}")
            except Exception as e:
                print("[WARNING] Redis连接失败，使用内存缓存: {e}")
                self.redis_client = None
        else:
            self.redis_client = None
            print("[INFO] 使用内存缓存")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        """
        try:
            # 尝试 Redis 缓存
            if self.redis_client:
                cached = self.redis_client.get(key)
                if cached:
                    print(f"[INFO] 从Redis缓存命中: {key[:50]}...")
                    return json.loads(cached)
            
            # 内存缓存
            if key in self.memory_cache:
                expiry = self.cache_expiry.get(key, 0)
                if expiry > time.time():
                    print(f"[INFO] 从内存缓存命中: {key[:50]}...")
                    return self.memory_cache[key]
                else:
                    # 清理过期缓存
                    del self.memory_cache[key]
                    if key in self.cache_expiry:
                        del self.cache_expiry[key]
                    print(f"[INFO] 缓存已过期: {key[:50]}...")
                        
        except Exception as e:
            print(f"[ERROR] 缓存获取错误: {e}")
        
        print(f"[INFO] 缓存未命中: {key[:50]}...")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置缓存数据
        """
        try:
            # 尝试 Redis 缓存
            if self.redis_client:
                result = self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, ensure_ascii=False)
                )
                if result:
                    print(f"[INFO] 数据已缓存到Redis: {key[:50]}... (TTL: {ttl}s)")
                return bool(result)
            
            # 内存缓存
            self.memory_cache[key] = value
            self.cache_expiry[key] = time.time() + ttl
            print(f"[INFO] 数据已缓存到内存: {key[:50]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            print(f"[ERROR] 缓存设置错误: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存数据
        """
        try:
            if self.redis_client:
                result = bool(self.redis_client.delete(key))
                if result:
                    print(f"[INFO] 已从Redis删除缓存: {key[:50]}...")
                return result
            
            if key in self.memory_cache:
                del self.memory_cache[key]
                if key in self.cache_expiry:
                    del self.cache_expiry[key]
                print(f"[INFO] 已从内存删除缓存: {key[:50]}...")
                return True
                
        except Exception as e:
            print(f"[ERROR] 缓存删除错误: {e}")
        
        return False
    
    def clear(self) -> bool:
        """
        清空所有缓存
        """
        try:
            if self.redis_client:
                result = bool(self.redis_client.flushdb())
                if result:
                    print("[INFO] 已清空Redis所有缓存")
                return result
            
            self.memory_cache.clear()
            self.cache_expiry.clear()
            print("[INFO] 已清空内存所有缓存")
            return True
            
        except Exception as e:
            print(f"[ERROR] 缓存清空错误: {e}")
            return False
import re
import spacy
from typing import Dict, Any, List
import os

class AIExtractor:
    def __init__(self):
        # 尝试加载spacy模型
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # 如果模型不存在，使用简单的规则
            self.nlp = None
            print("spacy model not found, using rule-based extraction")
        
        # 预定义技能关键词
        self.skill_keywords = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'],
            'web': ['html', 'css', 'react', 'vue', 'angular', 'django', 'flask', 'node.js', 'express', 'spring'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'sql'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github'],
            'ai_ml': ['tensorflow', 'pytorch', 'scikit-learn', 'nlp', 'computer vision', 'machine learning', 'deep learning'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'project management']
        }
    
    def extract_info(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取关键信息
        
        Args:
            text: 简历文本
            
        Returns:
            提取的信息字典
        """
        info = {
            "basic_info": self._extract_basic_info(text),
            "skills": self._extract_skills(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "summary": self._generate_summary(text)
        }
        return info
    
    def _extract_basic_info(self, text: str) -> Dict[str, str]:
        """
        提取基本信息
        """
        basic_info = {
            "name": "",
            "phone": "",
            "email": "",
            "location": ""
        }
        
        # 提取姓名（简单规则）
        lines = text.split('\n')
        for line in lines[:10]:  # 只检查前10行
            line = line.strip()
            # 检查是否像姓名（2-4个单词，没有特殊字符）
            if line and 2 <= len(line.split()) <= 4:
                if not any(char.isdigit() for char in line):
                    if not re.search(r'[@#\$%\^&\*\(\)]', line):
                        basic_info["name"] = line
                        break
        
        # 提取电话
        phone_patterns = [
            r'\+\d{1,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',
            r'\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                basic_info["phone"] = matches[0]
                break
        
        # 提取邮箱
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        if emails:
            basic_info["email"] = emails[0]
        
        # 提取地址
        location_keywords = ['street', 'avenue', 'road', 'st\.', 'ave\.', 'rd\.', 
                           'city', 'state', 'province', 'country', 'zip', 'postal']
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in location_keywords):
                # 提取可能的地址行
                address = sentence.strip()
                if len(address) > 10 and len(address) < 100:
                    basic_info["location"] = address
                    break
        
        return basic_info
    
    def _extract_skills(self, text: str) -> Dict[str, List]:
        """
        提取技能
        """
        skills = {
            "programming": [],
            "web": [],
            "databases": [],
            "cloud": [],
            "ai_ml": [],
            "soft_skills": [],
            "other": []
        }
        
        text_lower = text.lower()
        
        # 按类别提取技能
        for category, keywords in self.skill_keywords.items():
            found_skills = []
            for keyword in keywords:
                if keyword in text_lower:
                    found_skills.append(keyword.title())
            skills[category] = list(set(found_skills))
        
        return skills
    
    def _extract_experience(self, text: str) -> Dict[str, Any]:
        """
        提取工作经历
        """
        experience = {
            "years": self._estimate_experience_years(text),
            "companies": [],
            "roles": []
        }
        
        # 简单提取公司和职位
        lines = text.split('\n')
        experience_keywords = ['experience', 'work', 'employment', 'career', 'professional']
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # 寻找经历章节
            if any(keyword in line_lower for keyword in experience_keywords):
                # 检查接下来的几行
                for j in range(i+1, min(i+10, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and len(next_line) > 2:
                        # 简单的启发式规则
                        if any(role in next_line.lower() for role in 
                              ['engineer', 'developer', 'manager', 'analyst', 
                               'director', 'specialist', 'consultant']):
                            experience["roles"].append(next_line)
                        elif any(company in next_line.lower() for company in 
                                ['inc', 'ltd', 'corp', 'company', 'technologies', 'group']):
                            experience["companies"].append(next_line)
        
        # 去重
        experience["roles"] = list(set(experience["roles"]))[:5]
        experience["companies"] = list(set(experience["companies"]))[:5]
        
        return experience
    
    def _extract_education(self, text: str) -> Dict[str, Any]:
        """
        提取教育背景
        """
        education = {
            "degree": "",
            "university": "",
            "graduation_year": ""
        }
        
        education_keywords = ['university', 'college', 'institute', 'school', 
                            'bachelor', 'master', 'phd', 'doctor']
        
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords):
                education["university"] = line.strip()
                
                # 尝试提取学位
                degree_keywords = ['bachelor', 'master', 'phd', 'doctor', 
                                 'b.sc', 'm.sc', 'b.tech', 'm.tech', 'bs', 'ms']
                for degree in degree_keywords:
                    if degree in line_lower:
                        education["degree"] = degree.upper()
                        break
                
                # 尝试提取年份
                year_match = re.search(r'(19|20)\d{2}', line)
                if year_match:
                    education["graduation_year"] = year_match.group()
                
                break
        
        return education
    
    def _estimate_experience_years(self, text: str) -> int:
        """
        估算工作年限
        """
        # 查找日期模式
        date_pattern = r'(19|20)\d{2}'
        years = re.findall(date_pattern, text)
        
        if len(years) >= 2:
            years_int = [int(year) for year in years if 1900 < int(year) <= 2024]
            if years_int:
                min_year = min(years_int)
                max_year = max(years_int)
                return max(0, max_year - min_year)
        
        # 基于关键词估算
        experience_keywords = ['years', 'experience', 'experienced']
        for keyword in experience_keywords:
            pattern = rf'(\d+)\s*{keyword}'
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        # 基于角色和经验关键词估算
        senior_keywords = ['senior', 'lead', 'principal', 'architect', 'director']
        junior_keywords = ['junior', 'entry', 'fresh', 'graduate', 'intern']
        
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in senior_keywords):
            return 5
        elif any(keyword in text_lower for keyword in junior_keywords):
            return 1
        else:
            return 3  # 默认为中级
    
    def _generate_summary(self, text: str) -> str:
        """
        生成简历摘要
        """
        # 使用前300个字符作为摘要
        summary = text[:300].strip()
        if len(text) > 300:
            summary += "..."
        
        return summary
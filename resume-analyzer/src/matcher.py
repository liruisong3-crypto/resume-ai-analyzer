import re
from typing import Dict, Any, List
from collections import Counter

class ResumeMatcher:
    def __init__(self):
        # 常见技能关键词
        self.common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'react', 'vue', 'angular', 'node.js', 'django', 'flask', 'spring',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
            'machine learning', 'ai', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
            'agile', 'scrum', 'devops', 'ci/cd', 'git', 'rest api', 'microservices'
        ]
        
        # 岗位级别关键词
        self.level_keywords = {
            'senior': ['senior', 'lead', 'principal', 'architect', 'expert'],
            'mid': ['mid-level', 'intermediate', 'experienced'],
            'junior': ['junior', 'entry-level', 'associate', 'graduate']
        }
    
    def match(self, resume_info: Dict[str, Any], job_description: str, use_ai: bool = True) -> Dict[str, Any]:
        """
        匹配简历与岗位需求
        
        Args:
            resume_info: 简历信息
            job_description: 岗位描述
            use_ai: 是否使用AI匹配
            
        Returns:
            匹配结果
        """
        print("[INFO] 开始简历匹配分析...")
        
        # 提取岗位关键词
        job_keywords = self._extract_job_keywords(job_description)
        print(f"[INFO] 提取到 {len(job_keywords)} 个岗位关键词")
        
        # 计算技能匹配度
        skill_match = self._calculate_skill_match(resume_info['skills'], job_keywords)
        print(f"[INFO] 技能匹配度: {skill_match['percentage']}%")
        
        # 计算经验匹配度
        experience_match = self._calculate_experience_match(resume_info['experience'], job_description)
        print(f"[INFO] 经验匹配度: {experience_match['score']}/10")
        
        # 计算文本相似度
        text_similarity = self._calculate_text_similarity(
            resume_info['summary'],
            job_description[:500]  # 只比较前500字符
        ) if use_ai else 0.7
        print(f"[INFO] 文本相似度: {text_similarity:.1f}/10")
        
        # 综合评分
        overall_score = self._calculate_overall_score(
            skill_match,
            experience_match,
            text_similarity
        )
        print(f"[INFO] 综合评分: {overall_score}/10")
        
        # 生成反馈
        feedback = self._generate_feedback(
            overall_score,
            skill_match,
            experience_match,
            resume_info['skills']
        )
        
        return {
            "overall_score": round(overall_score, 1),
            "skill_match": skill_match,
            "experience_match": experience_match,
            "text_similarity": round(text_similarity, 1),
            "job_keywords": job_keywords[:20],  # 限制数量
            "feedback": feedback,
            "recommendation": self._get_recommendation(overall_score)
        }
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """
        从岗位描述中提取关键词
        """
        print("[INFO] 正在提取岗位关键词...")
        # 转换为小写
        text = job_description.lower()
        
        # 查找技能关键词
        found_keywords = []
        for skill in self.common_skills:
            if skill in text:
                found_keywords.append(skill)
        
        # 提取技术名词（连续大写字母或驼峰命名）
        tech_words = re.findall(r'\b[A-Z][a-z]+[A-Z][a-z]+\b', job_description)
        tech_words.extend(re.findall(r'\b[A-Z]{2,}\b', job_description))
        
        for word in tech_words[:10]:
            word_lower = word.lower()
            if word_lower not in found_keywords:
                found_keywords.append(word_lower)
        
        # 提取要求年限
        years_patterns = [
            r'(\d+)\+?\s*years?\s+experience',
            r'experience\s+of\s+(\d+)\+?\s*years?',
            r'(\d+)\s*-\s*\d+\s*years'
        ]
        
        for pattern in years_patterns:
            match = re.search(pattern, text)
            if match:
                found_keywords.append(f"experience_{match.group(1)}_years")
        
        print(f"[INFO] 提取完成，共 {len(found_keywords)} 个关键词")
        return list(set(found_keywords))
    
    def _calculate_skill_match(self, resume_skills: Dict[str, List], job_keywords: List[str]) -> Dict[str, Any]:
        """
        计算技能匹配度
        """
        # 扁平化简历技能
        all_resume_skills = []
        for category in resume_skills:
            all_resume_skills.extend([s.lower() for s in resume_skills[category]])
        
        all_resume_skills = list(set(all_resume_skills))
        
        print(f"[INFO] 简历技能数: {len(all_resume_skills)}, 岗位要求: {len(job_keywords)}")
        
        # 计算匹配的技能
        matched_skills = []
        for keyword in job_keywords:
            keyword_lower = keyword.lower()
            # 检查是否匹配
            for skill in all_resume_skills:
                if keyword_lower in skill or skill in keyword_lower:
                    matched_skills.append(keyword)
                    break
        
        # 计算匹配度
        if job_keywords:
            match_percentage = len(matched_skills) / len(job_keywords)
        else:
            match_percentage = 0
        
        print(f"[INFO] 技能匹配: {len(matched_skills)}/{len(job_keywords)} ({match_percentage*100:.1f}%)")
        
        return {
            "matched_skills": matched_skills,
            "missing_skills": [k for k in job_keywords if k not in matched_skills],
            "percentage": round(match_percentage * 100, 1),
            "score": round(match_percentage * 10, 1)  # 10分制
        }
    
    def _calculate_experience_match(self, experience: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        计算经验匹配度
        """
        # 提取岗位要求的经验年限
        years_required = self._extract_years_required(job_description)
        
        # 简历中的经验年限
        resume_years = experience.get('years', 0)
        
        print(f"[INFO] 岗位要求经验: {years_required}年, 简历实际经验: {resume_years}年")
        
        # 计算匹配度
        if years_required > 0:
            if resume_years >= years_required:
                match_score = 10.0
                print("[INFO] 经验要求完全满足")
            elif resume_years > 0:
                match_score = (resume_years / years_required) * 10
                match_score = min(10, match_score)
                print(f"[INFO] 经验匹配度: {match_score:.1f}/10")
            else:
                match_score = 0
                print("[WARNING] 无工作经验")
        else:
            # 如果没有明确要求，根据经验值给分
            if resume_years >= 8:
                match_score = 9.0
            elif resume_years >= 5:
                match_score = 7.5
            elif resume_years >= 3:
                match_score = 6.0
            elif resume_years >= 1:
                match_score = 4.0
            else:
                match_score = 2.0
            print(f"[INFO] 无明确经验要求，根据经验值评分: {match_score:.1f}/10")
        
        return {
            "years_required": years_required,
            "years_actual": resume_years,
            "score": round(match_score, 1),
            "match_level": self._get_experience_level(resume_years)
        }
    
    def _extract_years_required(self, job_description: str) -> int:
        """
        从岗位描述中提取所需经验年限
        """
        patterns = [
            r'(\d+)\+?\s*years',
            r'(\d+)\+?\s*years? experience',
            r'experience of (\d+)\+?\s*years',
            r'(\d+)\s*-\s*\d+\s*years'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description.lower())
            if match:
                return int(match.group(1))
        
        # 根据岗位级别推断
        text_lower = job_description.lower()
        if any(keyword in text_lower for keyword in self.level_keywords['senior']):
            return 5
        elif any(keyword in text_lower for keyword in self.level_keywords['mid']):
            return 3
        elif any(keyword in text_lower for keyword in self.level_keywords['junior']):
            return 1
        
        return 0  # 默认无要求
    
    def _calculate_text_similarity(self, resume_text: str, job_text: str) -> float:
        """
        计算文本相似度（简化的Jaccard相似度）
        """
        # 将文本转换为词集
        resume_words = set(resume_text.lower().split())
        job_words = set(job_text.lower().split())
        
        if not resume_words or not job_words:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(resume_words.intersection(job_words))
        union = len(resume_words.union(job_words))
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # 转换为10分制
        return similarity * 10
    
    def _calculate_overall_score(self, skill_match: Dict, experience_match: Dict, text_similarity: float) -> float:
        """
        计算综合评分
        """
        # 权重分配
        weights = {
            'skill': 0.5,
            'experience': 0.3,
            'similarity': 0.2
        }
        
        overall = (
            skill_match['score'] * weights['skill'] +
            experience_match['score'] * weights['experience'] +
            text_similarity * weights['similarity']
        )
        
        return round(overall, 1)
    
    def _get_experience_level(self, years: int) -> str:
        """
        获取经验等级
        """
        if years >= 8:
            return "Senior/Expert"
        elif years >= 5:
            return "Senior"
        elif years >= 3:
            return "Mid-level"
        elif years >= 1:
            return "Junior"
        else:
            return "Entry-level"
    
    def _generate_feedback(self, overall_score: float, skill_match: Dict, 
                          experience_match: Dict, skills: Dict) -> List[str]:
        """
        生成反馈建议
        """
        feedback = []
        
        # 总体评价
        if overall_score >= 8.5:
            feedback.append("[SUCCESS] 优秀匹配！该候选人非常适合此岗位。")
        elif overall_score >= 7.0:
            feedback.append("[SUCCESS] 良好匹配！该候选人基本符合岗位要求。")
        elif overall_score >= 5.0:
            feedback.append("[WARNING] 中等匹配！部分条件符合，建议进一步评估。")
        else:
            feedback.append("[FAILED] 匹配度较低！可能不适合此岗位。")
        
        # 技能反馈
        skill_percentage = skill_match['percentage']
        if skill_percentage >= 80:
            feedback.append(f"[SUCCESS] 技能匹配度优秀 ({skill_percentage}%)。")
        elif skill_percentage >= 60:
            feedback.append(f"[WARNING] 技能匹配度一般 ({skill_percentage}%)。")
        else:
            feedback.append(f"[FAILED] 技能匹配度不足 ({skill_percentage}%)。")
            if skill_match['missing_skills']:
                feedback.append(f"[INFO] 缺少技能: {', '.join(skill_match['missing_skills'][:3])}")
        
        # 经验反馈
        years_actual = experience_match['years_actual']
        years_required = experience_match['years_required']
        
        if years_required > 0:
            if years_actual >= years_required:
                feedback.append(f"[SUCCESS] 经验要求满足 ({years_actual}年)。")
            else:
                feedback.append(f"[WARNING] 经验略有不足: 需要{years_required}年，实际{years_actual}年。")
        else:
            feedback.append(f"[INFO] 候选人具有 {years_actual} 年工作经验。")
        
        # 建议
        if overall_score < 7.0:
            if skill_match['missing_skills']:
                missing = ', '.join(skill_match['missing_skills'][:3])
                feedback.append(f"[ADVICE] 建议: 考虑候选人是否具备学习以下技能的能力: {missing}")
        
        return feedback
    
    def _get_recommendation(self, score: float) -> str:
        """
        获取推荐等级
        """
        if score >= 8.5:
            return "强烈推荐"
        elif score >= 7.0:
            return "推荐"
        elif score >= 5.0:
            return "可考虑"
        else:
            return "不推荐"
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# ⚠️ الثوابت والأوزان ⚠️

# كلمات حيادية يتم تجاهلها عند المقارنة
STOP_WORDS = {
    "developer", "engineer", "specialist", "expert",
    "senior", "junior", "lead", "software", "professional", "dev", "development",
    "programmer", "coder", "technologist", "architect", "consultant", "programming", "master", "mastering",
}

# المجالات الأساسية (وزن 5)
CORE_FIELDS = {
    "frontend", "backend", "mobile", "ui", "ml",
    "devops", "data", "cloud", "security", "testing",
    "gamedev", "blockchain", "embedded", "pm"
}

# مجالات قريبة (وزن 2)
RELATED_FIELDS = {
    "api", "graphql", "rest", "microservices", "mvc", "orm"
}

# مرادفات + أدوات (وزن 1)
ALIASES = {
    # Backend Development
    "backend": {
        "django", "flask", "laravel", "spring", "express", "node", "rails", "fastapi", "nestjs",
        ".net", "php", "ruby", "python","jwt", "fullstack", "full-stack", "web",
    },

    # Frontend Development
    "frontend": {
        "react", "vue", "angular", "svelte", "next", "nuxt", "tailwind", "bootstrap",
        "html", "css", "javascript", "typescript", "sass", "less", "webpack", "babel",
        "fullstack", "full-stack", "web",
    },
    
    # ... (يجب إضافة بقية المفاتيح من الكود السابق: mobile, ui, ml, devops, etc.)
    "mobile": {
        "android", "ios", "flutter", "reactnative", "kotlin", "swift", "xcode", "jetpack", "expo","dart"
    },
    "ui": {
        "ux", "ui", "designer", "figma", "adobe", "xd", "sketch", "wireframe", "prototype", "usability", "designsystem","interactiondesign","visualdesign"
    },
    "ml": {
        "ai", "machine", "learning", "deep", "tensorflow", "pytorch", "sklearn", "nlp", "cv", "llm", "huggingface", "mlops",
    },
    "devops": {
        "docker", "kubernetes", "ci", "cd", "jenkins", "terraform", "ansible", "prometheus", "grafana", "helm", "argo", "sre"
    },
    "data": {
        "sql", "nosql", "mongodb", "postgres", "mysql", "bigquery", "redshift", "snowflake", "etl", "airflow", "dbt", "datawarehouse"
    },
    "cloud": {
        "aws", "azure", "gcp", "cloud", "lambda", "s3", "firebase", "cloudfunctions", "cloudrun", "cloudflare", "amplify"
    },
    "security": {
        "auth", "oauth", "jwt", "encryption", "ssl", "https", "firewall", "vulnerability", "pentest", "owasp", "sso"
    },
    "testing": {
        "jest", "mocha", "cypress", "unittest", "pytest", "selenium", "testcase", "qa", "integration", "e2e", "tdd", "bdd"
    },
    "gamedev": {
        "unity", "unreal", "godot", "gamemaker", "cocos", "shader", "opengl", "gamephysics", "leveldesign"
    },
    "blockchain": {
        "solidity", "web3", "ethereum", "smartcontract", "nft", "defi", "metamask", "truffle", "hardhat"
    },
    "embedded": {
        "arduino", "raspberry", "iot", "firmware", "circuit", "esp32", "microcontroller", "rtos"
    },
    "pm": {
        "scrum", "agile", "kanban", "jira", "trello", "roadmap", "backlog", "stakeholder", "productowner", "productmanager"
    }
}

ORIGINAL_WORD_BONUS = 3


# ⚠️ الدوال المساعدة ⚠️

def normalize_specialization(text):
    if not text:
        return set()

    text = text.lower()

    for ch in "&,/()-_":
        text = text.replace(ch, " ")

    words = set(text.split())

    return words - STOP_WORDS


def expand_words(words):
    expanded = set(words)

    for key, values in ALIASES.items():
        if key in words or words & values:
            expanded |= values
            expanded.add(key)

    return expanded


def similarity_score(words1_expanded, words2_expanded, words1_normalized, words2_normalized):
    """
    حساب التشابه الموزون (5/2/1) + منح مكافأة (3) للنية الأصلية + إضافة عامل عشوائي لكسر الثبات
    """
    intersection_expanded = words1_expanded & words2_expanded
    score = 0
    
    # 1. حساب الدرجة الموزونة العادية بناءً على التقاطع الموسع
    for w in intersection_expanded:
        if w in CORE_FIELDS:
            score += 5
        elif w in RELATED_FIELDS:
            score += 2
        else:
            score += 1

    # 2. منح مكافأة النية الأصلية (لزيادة دقة التطابق المباشر)
    original_intersection = words1_normalized & words2_normalized
    score += len(original_intersection) * ORIGINAL_WORD_BONUS

    # 3. كسر ثبات الترتيب (Tie-Breaker)
    random_tie_breaker = random.random() * 0.001 
    
    return score + random_tie_breaker
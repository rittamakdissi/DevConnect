# import torch
# from transformers import pipeline


# تحميل النموذج مرة واحدة فقط


# def improve_post_text(text):

#    # تحسين صياغة المنشور
#     generator =pipeline("text-generation", model="google/flan-t5-small", )

#     prompt = f"""
#     You are an assistant that writes clear and engaging social media posts.

#     Task:
#     Expand the user's idea into a well written post suitable for a developer community.

#     Rules:
#     - If the input text is in Arabic, write the response in Arabic.
#     - If the input text is in English, write the response in English.
#     - Keep the post clear and informative.
#     - Length should be 4 to 6 sentences.

#     User idea:
#     {text}
#     """

#     result = generator(prompt, max_length=120)

#     return result[0]["generated_text"]

# from transformers import pipeline

# # الموديل الخفيف
# MODEL_NAME = "google/flan-t5-small"

# def improve_post_text(text):
#     """
#     يحسن النص بنفس اللغة.
#     """
#     # pipeline خفيف فقط على CPU (device=-1)
   #  generator = pipeline(
   #      task="text-generation",
   #      model=MODEL_NAME,
   #      device=-1  # CPU فقط
   #  )

#     prompt = f"Improve this social media post while keeping the same language: {text}"

#     result = generator(prompt, max_length=200)

#     return result[0]["generated_text"]






# from transformers import pipeline

# MODEL_NAME = "google/flan-t5-small"
# generator = None  # lazy loading للموديل

# def improve_post_text(text):
#     global generator
#     if generator is None:
#         # تحميل الموديل فقط عند أول استخدام
#         generator = pipeline(
#             task="text-generation",  # استخدام pipeline خفيف
#             model=MODEL_NAME,
#              framework="tf",
#             device=-1  # CPU فقط
#         )
#     prompt = f"Improve this social media post while keeping the same language: {text}"
#     result = generator(prompt, max_length=120)
#     return result[0]["generated_text"]

# improve_post.py
# نسخة تجريبية للعرض على جهازك بدون PyTorch أو TensorFlow
# تدعم التجربة في مشروع التخرج مباشرة على CPU

# from transformers import AutoTokenizer, AutoModelForCausalLM
# import onnxruntime as ort

# MODEL_NAME = "google/flan-t5-small"
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# def improve_post_text(text):
#     """
#     دالة تجريبية للزر تحسين النص
#     ترجع النص نفسه مع "[النص محسّن]"
#     لاحقًا يمكن استبدالها بالموديل الفعلي لتحسين النص
#     """
#     return f"{text} [النص محسّن]"

# def improve_post_text(text):
#     """
#     دالة تجريبية لتجربة الزر على CPU فقط
#     تعيد النص نفسه + [النص محسّن]
#     """
#     return f"{text} [النص محسّن]"
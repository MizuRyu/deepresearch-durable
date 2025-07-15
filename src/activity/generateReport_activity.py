import azure.durable_functions as df

from loguru import logger

from function_app import app
from ..helpers.deduplicate_and_format_sources import deduplicate_and_format_sources

@app.function_name(name="generateReport_activity")
@app.activity_trigger(input_name="input")
async def generateReport_activity(
    input: dict
):
    logger.info("[generateReport_activity] Start Activity")
    # 画像ファイルがあれば使う
#     image_section = ""
#     images = []
#     if images and len(images) >= 2:
#         # Include the first two images at the top of the summary
#         image_section = f"""
# <div class="flex flex-col md:flex-row gap-4 mb-6">
#   <div class="w-full md:w-1/2">
#     <img src="{images[0]}" alt="Research image 1" class="w-full h-auto rounded-lg shadow-md">
#   </div>
#   <div class="w-full md:w-1/2">
#     <img src="{images[1]}" alt="Research image 2" class="w-full h-auto rounded-lg shadow-md">
#   </div>
# </div>
# """
#     elif images and len(images) == 1:
#         # If only one image is available, display it centered
#         image_section = f"""
# <div class="flex justify-center mb-6">
#   <div class="w-full max-w-lg">
#     <img src="{images[0]}" alt="Research image" class="w-full h-auto rounded-lg shadow-md">
#   </div>
# </div>
# """
    
    # report生成
    final_summary = input.get("final_summary", "")
    about_sources = input.get("sources", [])

    report_content = f"## Summary\n{final_summary}\n\n### Sources:\n"
    for source in about_sources:
        title = source.get('title', 'No Title')
        url = source.get('url', '#')
        report_content += f"- [{title}]({url})\n"

    logger.info("[generateReport_activity] End Activity")

    return report_content

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(generateReport_activity())
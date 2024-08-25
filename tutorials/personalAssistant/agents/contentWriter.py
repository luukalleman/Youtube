# ----------------------------------------
# Do imports
# ----------------------------------------
from llama_index.core.workflow import (
    Event, StartEvent, StopEvent, Workflow, step
)
from llama_index.llms.openai import OpenAI
import os
from dotenv import load_dotenv

# ----------------------------------------
# Load OpenAI API Key
# ----------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ----------------------------------------
# Define Custom Events
# ----------------------------------------
class DraftOutlineEvent(Event):
    outline: str

class WritePostEvent(Event):
    post_content: str

class ReviewContentEvent(Event):
    reviewed_content: str

# ----------------------------------------
# Define the Workflow: ContentWritingAgent
# ----------------------------------------
class ContentWritingAgent(Workflow):
    llm = OpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # ----------------------------------------
    # Step: Draft Content Outline
    # ----------------------------------------
    @step()
    async def draft_outline(self, ev: StartEvent) -> DraftOutlineEvent:
        prompt = f"""Create a detailed content outline for a social media post on the following topic: '{ev.get('data')}'. 
        The outline should include the key points and structure for an engaging and professional post. Use effective content strategies such as:
        - **99% of [Things] Lack**
        - **Development Stages in [Topic]**
        - **Myths About AI**
        - **Daily Insights and Lessons**
        - **Simplified Steps for Achieving Goals**
        - **Comparative Methods**
        use this tone of voice:
        1.	Balanced and Insightful: “Practical experience often provides deeper insights than traditional methods. Once the basics are mastered, diving into real-world applications can offer a more engaging and impactful learning journey.”
        2.	Encouraging and Reflective: “In my view, true understanding comes from hands-on work. Books are great, but the breakthroughs happen when you’re solving real problems.”
        3.	Forward-Looking and Optimistic: “I believe the future of education, especially in AI, lies in project-based learning. We’re already seeing this trend with bootcamps and online platforms that emphasize practical skills.”
        4.	Personal and Relatable: “From my own experience, the biggest leaps in my learning occurred when I was working on projects that were both enjoyable and practical. It’s in those moments that I truly grew.”
        5.	Action-Oriented: “Start with hands-on experience, and turn to theory as needed. This approach not only solidifies your knowledge but also makes learning more relevant and enjoyable.”
        6.	Engaging and Conversational: “What’s been your most significant learning experience? I’d love to hear your thoughts!”
 """
                
        outline = str(await self.llm.acomplete(prompt))
        return DraftOutlineEvent(outline=outline)
    
    # ----------------------------------------
    # Step: Write the Social Media Post
    # ----------------------------------------
    @step()
    async def write_post(self, ev: DraftOutlineEvent) -> WritePostEvent:
        prompt = f"""Based on the following outline, write a short, professional, and catchy social media post. 
        The post should be structured to capture attention quickly and deliver value efficiently.
        Outline: '{ev.outline}'"""
        
        post_content = str(await self.llm.acomplete(prompt))
        return WritePostEvent(post_content=post_content)

    # ----------------------------------------
    # Step: Review Content
    # ----------------------------------------
    @step()
    async def review_content(self, ev: WritePostEvent) -> ReviewContentEvent:
        prompt = f"""Review the following social media post for clarity, engagement, and structure. 
        Rewrite any parts that could be improved. If the content is already well-structured and ready as-is, 
        confirm it without adding extra text. The final output should be a clean, ready-to-post message with this tone of voice:
        1.	Balanced and Insightful: “Practical experience often provides deeper insights than traditional methods. Once the basics are mastered, diving into real-world applications can offer a more engaging and impactful learning journey.”
        2.	Encouraging and Reflective: “In my view, true understanding comes from hands-on work. Books are great, but the breakthroughs happen when you’re solving real problems.”
        3.	Forward-Looking and Optimistic: “I believe the future of education, especially in AI, lies in project-based learning. We’re already seeing this trend with bootcamps and online platforms that emphasize practical skills.”
        4.	Personal and Relatable: “From my own experience, the biggest leaps in my learning occurred when I was working on projects that were both enjoyable and practical. It’s in those moments that I truly grew.”
        5.	Action-Oriented: “Start with hands-on experience, and turn to theory as needed. This approach not only solidifies your knowledge but also makes learning more relevant and enjoyable.”
        6.	Engaging and Conversational: “What’s been your most significant learning experience? I’d love to hear your thoughts!”
        Post Content: '{ev.post_content}'"""
        
        reviewed_response = str(await self.llm.acomplete(prompt))
        
        # Extract the rewritten content or confirmation
        if "ready as-is" in reviewed_response.lower():
            reviewed_content = ev.post_content  # No changes needed
        else:
            reviewed_content = reviewed_response  # Use the revised content
        
        return ReviewContentEvent(reviewed_content=reviewed_content)
    
    # ----------------------------------------
    # Step: Output Final Content
    # ----------------------------------------
    @step()
    async def output_final_content(self, ev: ReviewContentEvent) -> StopEvent:
        # Return the reviewed content as the final result
        return StopEvent(result=ev.reviewed_content)


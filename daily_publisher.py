import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Morning Workout Routine to Start Your Day Strong",
        "5 Strength Exercises for a Confident, Capable Body",
        "Wellness Habits That Changed My Daily Life",
        "A Peaceful Morning Walk in Seoul to Clear Your Mind",
        "Home Workout: No Equipment, Full Body Burn",
        "How I Build Confidence Through Fitness",
        "Healthy Meal Prep for a Busy Week",
        "Stretching & Mobility for a Healthier Body",
        "My Everyday Wellness Routine in Seoul",
        "Cardio You'll Actually Enjoy",
        "Stronger Every Day: Progress Over Perfection",
        "Self-Care Rituals for a Balanced Lifestyle",
        "Leg Day Essentials for Strength & Stability",
        "Finding Calm in the City: My Seoul Reset",
        "Fitness Inspiration for Total Beginners",
    ]

    fallback_descriptions = [
        "Strength isn't built in a day — it's built in the small choices you make daily. This morning routine wakes up your body and your mindset. Save it for tomorrow! 💪 #fitness #workout #morningroutine #strength #kimchaewonya",
        "A strong body carries you through life with confidence. These five moves need no gym — just your own weight and consistency. Like if you're starting your strength journey! 🏋️ #strengthtraining #fitness #wellness #confidence #kimchaewonya",
        "Wellness is more than workouts — it's sleep, hydration, calm, and kindness to yourself. Tiny habits, big difference. Comment your favorite wellness habit! 🌿 #wellness #healthyliving #selfcare #lifestyle #kimchaewonya",
        "Some of my best ideas come on a slow walk through Seoul. Fresh air, quiet streets, and movement clear my mind like nothing else. Double tap if you love a peaceful reset! 🇰🇷 #seoul #walk #mindfulness #lifestyle #kimchaewonya",
        "No gym? No problem. This full-body home workout gets your heart up using just your body. Try it between meetings! Save this for later! 🔥 #homeworkout #fitness #cardio #noexcuses #kimchaewonya",
        "Confidence grows when you show up for yourself. Every workout is proof you can do hard things. Drop a 💪 if you're building confidence too! #confidence #fitness #selflove #stronger #kimchaewonya",
        "Fuel your body, fuel your life. A little meal prep on Sunday keeps my week healthy and stress-free. Like if you want the full recipe! 🥗 #mealprep #nutrition #healthyeating #wellness #kimchaewonya",
        "Mobility is freedom. A few minutes of stretching each day keeps your body loose and happy. Save this routine! 🧘 #stretching #mobility #recovery #wellness #kimchaewonya",
        "My Seoul days blend movement, calm, and little joys — a workout, a good meal, golden-hour light. Follow Kim Chaewonya for daily fitness, wellness, and lifestyle inspiration! 🌸 #seoul #lifestyle #wellness #fitness #kimchaewonya",
        "Cardio doesn't have to be punishment. Put on a song you love and just move — joy is the best motivator. Comment your favorite workout song! 🎶 #cardio #fitness #funworkout #wellness #kimchaewonya",
        "Progress over perfection. Every rep, every walk, every healthy choice adds up. Stronger every day, inside and out. Double tap if you agree! ✨ #progress #fitness #wellness #motivation #kimchaewonya",
        "Self-care isn't selfish — it's how you stay full. A warm bath, early sleep, a slow morning. Protect your peace. Like if you're prioritizing balance! 🛁 #selfcare #balance #lifestyle #wellness #kimchaewonya",
        "Leg day builds the foundation for everything. Strength, stability, and confidence start from the ground up. Save this for your next session! 🦵 #legday #strengthtraining #fitness #lowerbody #kimchaewonya",
        "The city can be calming if you know where to look. My Seoul reset: a quiet café, a park bench, deep breaths. Comment what helps you reset! 🌿 #seoul #reset #mindfulness #lifestyle #kimchaewonya",
        "Starting fitness can feel scary — begin with one walk, one stretch, one choice. You don't need to be perfect, just begin. Follow Kim Chaewonya for gentle, daily inspiration! 🌟 #fitnessforbeginners #wellness #lifestyle #kimchaewonya",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "energetic and motivating — make viewers want to move their body now",
        "calm and wellness-focused — emphasise balance, recovery, and self-care",
        "confident and empowering — celebrate strength and self-belief",
        "practical and coach-like — give honest fitness and nutrition tips",
        "personal and inspiring — share real routines and small daily wins",
        "Seoul-local — weave in city life, cafés, parks, and everyday moments",
        "uplifting — encourage consistency and a healthier lifestyle",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Kim Chaewonya'. "
        f"A space for fitness, wellness, and lifestyle — building strength, confidence, and a healthier life, based in Seoul, South Korea. It's energetic, empowering, and speaks to people who want to feel stronger inside and out through fitness routines, wellness habits, and everyday inspiration. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this motivated your workout! Comment your fitness goal below! Share this with a friend who needs a boost! Follow Kim Chaewonya for daily fitness, wellness, and lifestyle inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #fitness #wellness #lifestyle #workout #strength #seoul #healthyliving #motivation #kimchaewonya. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["fitness", "wellness", "lifestyle", "workout", "strength", "seoul", "healthyliving", "motivation", "kimchaewonya", "homeworkout", "selfcare", "korea", "fitnesstips", "health"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()

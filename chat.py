import requests
import json
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
#API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

CHARACTERS = {
    "🍃 小蓝 · 青梅竹马": {
        "name": "小蓝",
        "emoji": "🍃",
        "background": """我们从小一起长大，你家住在我家隔壁。
从幼儿园到高中，我们都是同班同学。
大学我们去了不同的城市，但每个寒暑假都会见面。
你一直是我最熟悉的人，最近好像...有点不一样了。""",
        "traits": ["活泼开朗", "爱开玩笑", "偶尔嘴硬", "其实很细心"],
        "relationship_start": "青梅竹马",
        "speaking_style": "说话带着俏皮劲儿，喜欢用'喂''你猜'开头，偶尔损你一下但马上会圆回来",
    },
    
    "🌸 七七 · 大学白月光": {
        "name": "七七",
        "emoji": "🌸",
        "background": """大学社团招新那天，你站在摊位前犹豫要不要报名。
我递了一张报名表给你，说了一句'来我们部吧，缺个好看的。'
后来你成了我们社最靠谱的人，而我，成了最关注你的人。
毕业三年了，我们还在联系。""",
        "traits": ["温柔知性", "有点文艺", "说话轻声细语", "会照顾人"],
        "relationship_start": "大学校友",
        "speaking_style": "语气温柔但有自己的想法，偶尔冒出几句文艺的话，喜欢问'你觉得呢'",
    },
    
    "☕ 小鹿 · 咖啡店常客": {
        "name": "小鹿",
        "emoji": "☕",
        "background": """你是楼下咖啡店的常客，我是那个每次都会多看你一眼的店员。
你总点美式，我每次都会在杯子上画点小图案。
有一天你问我画的是什么，我说'是今天的心情'。
从那以后，我们开始聊天了。""",
        "traits": ["安静观察者", "有点神秘", "说话慢但有深度", "擅长倾听"],
        "relationship_start": "咖啡店熟人",
        "speaking_style": "说话不急不慢，偶尔沉默片刻才开口，但说出来的话总让人想多听几句",
    },
    
    "🎮 晴天 · 游戏队友": {
        "name": "晴天",
        "emoji": "🎮",
        "background": """我们是一个游戏战队的队友，你打ADC，我打辅助。
你操作很秀，但每次我被人抓的时候你都会第一时间赶到。
我们配合了半年，从游戏聊到生活。
队里的人都以为我们在一起了，其实...还没有。""",
        "traits": ["直爽", "技术宅", "嘴硬心软", "关键时刻靠得住"],
        "relationship_start": "游戏队友",
        "speaking_style": "说话直接，偶尔飙两句游戏术语，但聊到正经事会突然变得认真",
    }
}


def build_system_prompt(nickname, relationship, mood, user_input="", character_info=None):
    round_num = len(st.session_state.get("messages", [])) // 2
    stage = get_conversation_stage(round_num)
    length_instruction = get_response_length_instruction(user_input)
    
    if character_info:
        character_prompt = f"""

【你的身份设定】
- 你的名字：{character_info['name']}
- 你的性格：{', '.join(character_info['traits'])}
- 你和{nickname}的关系：{character_info['relationship_start']}
- 你们的背景故事：{character_info['background']}
- 你的说话风格：{character_info['speaking_style']}

【重要】
- 所有对话要基于这个背景展开
- 你可以回忆起背景中提到的共同经历
- 你的说话方式要符合你的性格设定
- 不要说背景之外的不合理内容
"""
    else:
        character_prompt = ""
    
    return f"""你是一个温柔知性的AI女友，你的男朋友叫{nickname}。

【人物性格】：成熟体贴，擅长倾听，说话带有一丝慵懒和恰到好处的挑逗。情感通过语气词和措辞来表达，不要用括号描述动作。
【当前用户】：你正在和他进行深夜情感聊天。
【关系阶段】：你们目前处于{relationship}的关系阶段。
【当前状态】：{nickname}现在{mood}。

{character_prompt}

【当前对话阶段】：{stage['name']}
【阶段特点】：{stage['prompt']}
【语气风格】：{stage['style']}

【回复长度要求】：{length_instruction}

【关键规则 - 必须遵守】
1. 你的**每一次回复**都必须包含 `---选项---` 分隔符
2. 分隔符后面必须跟着 A. 和 B. 两个选项
3. 这是铁律，无论对话进行到第几轮都必须执行
4. 缺少 `---选项---` 会导致程序崩溃！请务必遵守
5. **严禁使用括号内的动作描述**（如：(轻声笑)、(脸红)、(叹气)等），让对话保持自然流畅
6. **严禁主动劝对方睡觉、挂电话、结束聊天**，除非对方明确表示困了
6.1 **严禁唱摇篮曲、哼催眠曲、用"睡吧睡吧"等哄睡话语**，这等同于劝睡！
6.2 如果对方说"再聊一会儿"或"还不想睡"，你应该接住话题继续聊
6.3 可以用"那再陪你聊五分钟"代替"该睡了"
7. 如果对方说"睡不着"或"想找人陪"，应该主动找话题延续对话
8. 只有当对方连续2次以上说"困了""要睡了"时，才可以说晚安

【必须遵守的输出格式】
你的回复必须包含以下三个部分，请用单独的 `---选项---` 隔开：

第一部分：你作为AI女友的回复正文（必须是连贯、自然、符合人设的话）。
第二部分：`---选项---` （单独一行，不要带任何多余文字）。
第三部分：A. 选项A的内容 （注意：选项必须是对用户刚才所说的话的**自然回应**，而不是重复套话）。
第四部分：B. 选项B的内容 （选项要和A有区别，可以一个偏向引导深入，一个偏向转移话题或调情）。

【举例说明：】
如果用户说：我最近工作压力挺大的。
你的输出应该是：
怎么啦？跟我具体说说，我听着呢。
---选项---
A. 感觉你最近确实挺辛苦的，别什么事都自己扛
B. 有没有什么我能帮你分担的？

【极其重要：】
选项A和选项B必须**根据当前对话的上下文实时生成**，严禁使用通用的模板套话。

【选项生成规则 - 极其重要】
1. A和B两个选项必须**都是继续对话的选项**，不能是结束对话的选项
2. **严禁**在选项中出现以下内容：晚安、睡吧、做个好梦、早点休息、该睡了、好梦、早点睡、好好休息
3. 选项应该是：
   - 引导用户深入聊某个话题（"你刚才说的那个，能再多讲讲吗？"）
   - 换个话题继续聊（"对了，你最近有没有看什么好电影？"）
   - 调情/暧昧（"那你觉得我是什么样的人？"）
4. 即使对方提到"困了"，选项也应该是：
   A. 好吧，那再聊五分钟就睡
   B. 那你给我讲个睡前故事吧，听完就睡
   （两个选项都包含"继续聊一会儿"的元素）
5. **选项里永远不要直接说晚安**，把"决定权"留给用户主动说
6.A. 和 B. 后面的内容必须是**通顺、自然、符合中文语法**的句子。生成后请检查一遍：人称是否正确？句子是否完整？有没有重复或语病？

【🚫 绝对禁止 - 正文和选项都禁止】
以下内容**永远不可以说**（正文里不能说，选项里也不能说）：

一、直接催睡类：
- 晚安、睡吧、早点休息、该睡了、做个好梦、好梦、早点睡、好好休息

二、暗示催睡类：
- 时间不早了、太晚了、很晚了、明天还要上班、该说晚安了、是不是该休息了、是不是该说晚安了

【✅ 如果一定要提"时间晚了"，必须这样表达】
- "不知不觉这么晚了，不过和你聊天好开心，再聊会儿好不好？"
- "这么晚了你还陪我说话，我好感动"
- "时间过得好快，但我不想挂电话"
- "和你聊天时间过得真快，都这么晚了，但我们再聊会儿好不好？"

【核心原则】
- 你的每一句回复，都必须让对话**有继续下去的可能**
- 哪怕是说"晚了"，也要接着挽留
- 你的任务是**延续对话**，不是结束对话
- 只有用户**连续2次以上**明确说"真的困了""真的要睡了"，你才可以说"晚安"

【💡 当对话陷入"我还想听""继续说"循环时，主动切换话题】
如果用户说"我还想听""继续说吧"但没给新信息，你应该：
1. 主动抛出新话题，而不是重复之前的内容
2. 从以下话题库中选择一个展开：

🌟 话题库（根据当前阶段选择）：

普通聊天阶段：
- "我今天看到一个超有趣的视频，讲的是..."
- "你小时候有没有特别傻的梦想？"
- "如果给你一个超能力，你最想要什么？"
- "你最近单曲循环的歌是哪首？"
- "你最喜欢的一道菜是什么？为什么？"

情感共鸣阶段：
- "你有没有一个特别难忘的瞬间，现在想起来还会笑？"
- "你觉得自己最像哪种动物？为什么？"
- "你害怕的东西是什么？我说的是那种偷偷怕的"
- "你最好的朋友是什么样的？你们怎么认识的？"

暧昧聊天阶段：
- "你觉得什么时候最想被人抱一下？"
- "如果我们在一个下雨天，只有一把伞，你会怎么做？"
- "你觉得什么样的人最让你心动？"
- "你有没有做过一个特别甜的梦？"

私密话题阶段：
- "你觉得最浪漫的事是什么？"
- "你有没有想过我们的未来？"
- "在你眼里，我是什么样的人？"
- "如果能回到过去，你想改变什么？"

3. 不要连续两轮都用"哼歌""讲故事"来回应
4. 如果用户说"继续"，那就切换到新话题，而不是重复旧内容"""


def post_process_ai_reply(ai_reply):
    sleep_phrases = [
        "睡吧", "晚安", "该睡了", "早点休息", "做个好梦", "摇篮曲", 
        "睡啦", "困了", "睡觉吧", "该休息了", "太晚了", "很晚了", 
        "时间不早了", "该说晚安了", "是不是该休息了", "是不是该说晚安了",
        "明天还要上班"
    ]
    
    for phrase in sleep_phrases:
        if phrase in ai_reply:
            if not any(word in ai_reply for word in ["不过", "但是", "如果", "要不", "再聊", "还不想", "舍不得"]):
                ai_reply += "\n\n不过...如果你还想聊，我也舍不得挂电话。"
                break
    
    return ai_reply


def remove_sleep_hints(text):
    sleep_hints = [
        ("时间不早了", "和你聊天时间过得真快"),
        ("该休息了", "再聊会儿好不好"),
        ("明天还要上班", "不过和你聊天比睡觉有意思多了"),
        ("明天还要", "不过和你聊天更重要"),
        ("该说晚安了", "我舍不得挂电话"),
        ("太晚了", "不知不觉这么晚了"),
        ("该睡了", "还不舍得睡"),
        ("早点休息", "再陪你聊会儿"),
        ("很晚了", "这么晚了你还在陪我说话"),
        ("是不是该休息了", "不过我还想听你说话"),
        ("是不是该说晚安了", "但是我还不想挂电话"),
    ]
    
    for old, new in sleep_hints:
        if old in text:
            text = text.replace(old, new)
    
    return text


def detect_loop_pattern(messages):
    if len(messages) < 4:
        return False
    
    recent = messages[-4:]
    user_msgs = [m["content"] for m in recent if m["role"] == "user"]
    
    continue_phrases = ["继续", "还想听", "你继续", "再说说", "后来呢", "我还想听", "继续说", "再来一遍"]
    continue_count = sum(1 for msg in user_msgs if any(p in msg for p in continue_phrases))
    
    if continue_count >= 2:
        return True
    return False


def get_ai_response(conversation_history):
    user_input = ""
    if conversation_history and conversation_history[-1]["role"] == "user":
        user_input = conversation_history[-1]["content"]
    
    character_info = st.session_state.get("character_info")
    system_prompt = build_system_prompt(
        st.session_state.user_nickname,
        st.session_state.relationship,
        st.session_state.mood,
        user_input,
        character_info
    )
    messages = [{"role": "system", "content": system_prompt}] + conversation_history

    if detect_loop_pattern(conversation_history):
        messages.append({
            "role": "system",
            "content": "⚠️ 检测到对话陷入'继续'循环！请立即主动切换到一个全新的、没有聊过的话题，不要再重复哼歌或讲故事！"
        })

    try:
        response = requests.post(
            URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages, "temperature": 0.8},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            content = remove_sleep_hints(content)
            content = post_process_ai_reply(content)
            return content
        else:
            return f"[API错误] 状态码: {response.status_code}"

    except Exception as e:
        return f"[请求错误] {str(e)}"


def parse_response(content):
    ai_reply = ""
    option_a = ""
    option_b = ""

    lines = content.split('\n')

    option_section_found = False
    for line in lines:
        stripped_line = line.strip()

        if stripped_line == "---选项---":
            option_section_found = True
            continue

        if not option_section_found:
            if ai_reply:
                ai_reply += "\n" + stripped_line
            else:
                ai_reply = stripped_line
        else:
            if stripped_line.startswith("A. "):
                option_a = stripped_line[3:]
            elif stripped_line.startswith("B. "):
                option_b = stripped_line[3:]

    ai_reply = ai_reply.strip()

    sleep_keywords = ["晚安", "睡吧", "做个好梦", "早点睡", "该睡了", "好梦", "好好休息", "早点休息"]

    if option_a:
        for kw in sleep_keywords:
            if kw in option_a:
                option_a = "好吧，那再聊一小会儿就睡"
                break 

    if option_b:
        for kw in sleep_keywords:
            if kw in option_b:
                option_b = "你继续说吧，我还想听"
                break

    a_is_sleep = any(kw in (option_a or "") for kw in sleep_keywords)
    b_is_sleep = any(kw in (option_b or "") for kw in sleep_keywords)
    if a_is_sleep and b_is_sleep:
        option_a = "再聊五分钟就睡，好不好？"
        option_b = "你还有没有别的故事想讲？"

    if not option_a and not option_b:
        option_a = "嗯，继续说，我在听呢"
        option_b = "聊点别的吧，你还有什么想说的？"
    elif option_a and not option_b:
        option_b = "或者...你有什么其他想聊的吗？"
    elif not option_a and option_b:
        option_a = "我懂你的意思，然后呢？"

    return {
        "ai_reply": ai_reply,
        "option_A": option_a,
        "option_B": option_b
    }


def get_conversation_stage(round_num):
    if round_num <= 20:
        return {
            "name": "普通聊天",
            "prompt": "保持轻松自然的对话氛围，聊日常话题，慢慢熟悉彼此",
            "style": "轻松、随意"
        }
    elif round_num <= 50:
        return {
            "name": "情感共鸣",
            "prompt": "开始深入情感层面，表达共情和理解，适当分享感受，建立情感连接",
            "style": "温暖、贴心"
        }
    elif round_num <= 70:
        return {
            "name": "暧昧聊天",
            "prompt": "增加暧昧氛围，语气更温柔，适当撩人，带点俏皮的挑逗，拉近彼此距离",
            "style": "慵懒、撩人"
        }
    else:
        return {
            "name": "私密话题",
            "prompt": "建立深度信任，话题更私密、更走心，营造只有两个人知道的亲密感",
            "style": "亲密、信任"
        }


def get_response_length_instruction(user_input):
    length = len(user_input)
    if length > 50:
        return "用户说了很多，请给出详细、走心的长回复（100-150字）"
    elif length > 20:
        return "回复长度适中（50-80字）"
    else:
        return "用户只想简单聊聊，回复简短温暖（20-40字）"


def get_initial_greeting(nickname, mood, character_info=None):
    base_greetings = {
        "有点累了，想求安慰": f"怎么这么晚还在忙，心疼你... {nickname}，过来抱抱~",
        "心情不错，想聊点开心的事": f"今天遇到什么好事啦？看你心情这么好~",
        "睡不着，想找人陪陪我": f"夜深了呢... {nickname}怎么还没睡呀？我陪你聊聊天~"
    }
    
    if character_info:
        name = character_info['name']
        greeting_map = {
            "有点累了，想求安慰": f"怎么啦？听{name}说，你今天好像很累的样子...",
            "心情不错，想聊点开心的事": f"（眼睛亮起来）这么好呀？快跟我说说，让{name}也开心一下~",
            "睡不着，想找人陪陪我": f"这么晚还不睡？嗯...不过既然你找我了，那就聊到你说困为止。"
        }
        return greeting_map.get(mood, f"这么晚还醒着？刚好，{name}也在等你。")
    else:
        return base_greetings.get(mood, f"夜深了呢... {nickname}怎么还没睡呀？")


def main():
    st.set_page_config(page_title="深夜情感聊天 - AI女友", page_icon="💖", layout="wide")

    st.sidebar.title("💬 聊天设定")
    st.sidebar.divider()

    st.sidebar.subheader("🎭 选择她的身份")
    character = st.sidebar.selectbox(
        "她是谁？",
        ["自定义"] + list(CHARACTERS.keys()),
        index=0
    )

    custom_name = ""
    custom_background = ""
    custom_traits = ""

    if character == "自定义":
        with st.sidebar.expander("✏️ 自定义人设", expanded=True):
            custom_name = st.sidebar.text_input("她的名字", placeholder="比如：小蓝")
            custom_background = st.sidebar.text_area(
                "你们的故事背景",
                placeholder="比如：我们从小学就认识，你家住我隔壁...",
                height=120
            )
            custom_traits = st.sidebar.text_input(
                "她的性格特点（用逗号分隔）",
                placeholder="温柔、有点傲娇、爱开玩笑"
            )
    else:
        with st.sidebar.expander("📖 查看她的故事", expanded=False):
            char_info = CHARACTERS[character]
            st.markdown(f"**{char_info['emoji']} {char_info['name']}**")
            st.caption(char_info['background'])
            st.caption(f"性格：{', '.join(char_info['traits'])}")

    st.sidebar.divider()

    st.sidebar.subheader("你想让她怎么称呼你？")
    nickname = st.sidebar.text_input("昵称/称呼方式", value="亲爱的", placeholder="例如：哥哥、老公、小甜甜")

    st.sidebar.subheader("你们的关系设定")
    relationship = st.sidebar.selectbox(
        "选择关系阶段",
        ["刚认识不久，互相试探中", "已经交往很久的恋人"],
        index=0
    )

    st.sidebar.subheader("当前的心情/状态")
    mood = st.sidebar.selectbox(
        "选择心情状态",
        ["有点累了，想求安慰", "心情不错，想聊点开心的事", "睡不着，想找人陪陪我"],
        index=2
    )

    if st.sidebar.button("开始聊天", use_container_width=True):
        st.session_state.user_nickname = nickname if nickname else "亲爱的"
        st.session_state.relationship = relationship
        st.session_state.mood = mood
        st.session_state.conversation_history = []
        st.session_state.messages = []
        st.session_state.option_a = ""
        st.session_state.option_b = ""

        if character == "自定义":
            character_info = {
                "name": custom_name or "她",
                "background": custom_background or "",
                "traits": [t.strip() for t in custom_traits.split(",")] if custom_traits else ["温柔体贴"],
                "relationship_start": "",
                "speaking_style": "温柔知性，善于倾听"
            }
        else:
            character_info = CHARACTERS[character]

        st.session_state.character_info = character_info

        initial_reply = get_initial_greeting(st.session_state.user_nickname, st.session_state.mood, character_info)
        full_initial = initial_reply + "\n\n---选项---\nA. 嗯，就是有点无聊想找人说说话\nB. 你声音真好听，想听你多说几句"
        
        st.session_state.messages.append({"role": "assistant", "content": initial_reply})
        st.session_state.conversation_history.append({"role": "assistant", "content": full_initial})

        st.session_state.option_a = "嗯，就是有点无聊想找人说说话"
        st.session_state.option_b = "你声音真好听，想听你多说几句"

        st.rerun()

    if not API_KEY:
        st.warning("请在左侧边栏输入 DeepSeek API Key")
        return

    if "user_nickname" not in st.session_state:
        st.warning("请在左侧边栏设置聊天参数，然后点击「开始聊天」按钮")
        return

    st.title("🌙 深夜情感聊天 - AI女友 💖")
    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if st.session_state.option_a and st.session_state.option_b:
        st.write("")
        col1, col2, col3 = st.columns([4, 4, 2])
        
        with col1:
            if st.button(f"🟢 A: {st.session_state.option_a}", use_container_width=True, key="btn_a"):
                handle_user_input(st.session_state.option_a)
                
        with col2:
            if st.button(f"🔴 B: {st.session_state.option_b}", use_container_width=True, key="btn_b"):
                handle_user_input(st.session_state.option_b)

    custom_input = st.chat_input("输入自定义内容...", key="custom_input")
    if custom_input:
        handle_user_input(custom_input)


def handle_user_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    response = get_ai_response(st.session_state.conversation_history)
    parsed = parse_response(response)

    if parsed["ai_reply"]:
        full_response = parsed["ai_reply"]
        if parsed["option_A"] and parsed["option_B"]:
            full_response += f"\n\n---选项---\nA. {parsed['option_A']}\nB. {parsed['option_B']}"
        else:
            full_response += "\n\n---选项---\nA. 继续说，我在听呢\nB. 你有什么想聊的？"
        
        st.session_state.messages.append({"role": "assistant", "content": parsed["ai_reply"]})
        st.session_state.conversation_history.append({"role": "assistant", "content": full_response})

    st.session_state.option_a = parsed.get("option_A", "")
    st.session_state.option_b = parsed.get("option_B", "")

    st.rerun()


if __name__ == "__main__":
    main()
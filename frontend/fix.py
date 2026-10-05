cd C:\Users\Malak\zero-stockout\frontend
python -c @"
import re
path = 'app.py'
src = open(path, encoding='utf-8').read()

# 1. Remove ANY broken try: blocks around streamlit_webrtc
src = re.sub(
    r'try:\s*\n\s*from streamlit_webrtc import[^\n]*\n(?!\s*except)',
    '# WebRTC disabled (Python 3.14 has no compatible wheels)\nwebrtc_streamer = None\nWebRtcMode = None\nRTCConfiguration = None\n',
    src
)

# 2. Remove dangling 'try:' before streamlit_webrtc
src = re.sub(
    r'try:\s*\n(\s*)from streamlit_webrtc import[^\n]*\n',
    r'\1# WebRTC disabled\n\1webrtc_streamer = None\n\1WebRtcMode = None\n\1RTCConfiguration = None\n',
    src
)

# 3. Neutralize any remaining streamlit_webrtc import (plain, no try)
src = re.sub(
    r'^\s*from streamlit_webrtc import[^\n]*$',
    '# WebRTC disabled\nwebrtc_streamer = None\nWebRtcMode = None\nRTCConfiguration = None',
    src, flags=re.MULTILINE
)

# 4. Neutralize 'import av'
src = re.sub(r'^\s*import av\s*$', 'av = None  # disabled', src, flags=re.MULTILINE)

# 5. Comment out any webrtc_streamer(...) CALLS (replace call with pass)
src = re.sub(
    r'^(\s*)webrtc_streamer\(',
    r'\1pass  # webrtc_streamer disabled\n\1if False: webrtc_streamer(',
    src, flags=re.MULTILINE
)

open(path, 'w', encoding='utf-8').write(src)
print('✅ app.py patched successfully')
print('Lines changed: webrtc imports neutralized, av disabled, webrtc_streamer calls no-op')
"@
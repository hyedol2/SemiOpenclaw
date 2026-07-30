Openclaw(오픈클로)란?

Openclaw는 AI API를 연동하여 내가 원하는 AI로 컴퓨터의 권한을 모두 AI에게 맡기는 것입니다. 쉽게 말해 AI비서이지요

이 Openclaw는 설치할 때 관리자 권한을 요구하지 않지만 Openclaw내에서 wsl2(Windows Subsystem for Linux) 설치를 요구하며 이것을 설치할 때 관리자 권한이 요구됩니다. 또, Openclaw의 UI가 너무 복잡합니다.

​

그래서 제가 Openclaw를 만들었습니다. 간단하게 만들어서 제대로 작동하지 않을 수도 있고 Too Many Requests 오류가 많이 뜹니다.(포크해서 고쳐주세요) 하지만 기존 Openclaw의 기능들은 대부분 있고, AI API 3개를 등록할 수 있습니다. (gemini, openrouter, nvidia) 

https://github.com/hyedol2/SemiOpenclaw


GitHub - hyedol2/SemiOpenclaw: Openclaw but i made
Openclaw but i made. Contribute to hyedol2/SemiOpenclaw development by creating an account on GitHub.

github.com

사용 방법

.env 파일 또는 환경변수(AI이름_API_KEY)로 API 키를 정해주고 그에 맞는 AI를 선택하시면 바로 사용할 수 있습니다(매우 쉽습니다) main.py 를 실행하여 Openclaw를 사용해보세요!

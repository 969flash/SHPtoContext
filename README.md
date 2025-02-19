"Feb 18, 2025"
더 쉬운 설치방법 :
1. Rhino 8 (라이노7 혹은 라이노8 초기버전은 안된다) 설치
2. PackageMangaer 명령어 실행
3. VworldTo3D 설치
-  ![image](https://github.com/user-attachments/assets/8095951b-21fb-49d1-adc0-35abc9032ffd)
4. 라이노 재실행
5. Grasshopper 실행 후 VworldTo3D 탭 확인후 컴퍼넌트 사용
6. zip 파일(여러 파일도 상관없음)을 링크한 파일 컴퍼넌트 연결 후 사용

"Dec 18, 2024 "

준비물
1. Rhino 8
2. pyshp (https://github.com/hiteca/ghshp#install-pyshp)

Install pyshp

Plugin developed for using in native python environment while Grasshopper is using IronPython. So installation of the module requires a bit of creativity.

Download pyshp zip achive https://github.com/GeospatialPython/pyshp/archive/1.2.12.zip

Extract it to C:\Users\%USERNAME%\AppData\Roaming\McNeel\Rhinoceros\8.0\scripts. Final path to shapefile.py should be ...Rhinoceros\8.0\scripts\shapefile.py

3. Vworld로 부터 5000:1 수치지형도 ver2.0 을 다운받는다(zip file). (https://map.vworld.kr/map/dtkmap.do?mode=MAPW201)
![image](https://github.com/user-attachments/assets/5b7d5a8a-bb0c-4c62-847d-29e8e68b6184)


사용법

1. 다운 받은 zip파일을 압축해제하지 않고 path에 연결한다.

   ![image](https://github.com/user-attachments/assets/69256e51-10ce-4a7b-aac1-b3a70121e020)

3. 기다린다.
4. 끝

   ![image](https://github.com/user-attachments/assets/242f7e9b-c019-4f28-9b6a-6d9274a575d3)










* 스크립트 실행 불가시,
* ![image](https://github.com/user-attachments/assets/f90671ae-a09b-42fe-b693-fd9ae69fc282)
* ![image](https://github.com/user-attachments/assets/5eb710c0-24bf-426e-a134-2342c4617cf8)

* 아래와같이 main.py 파이썬 파일을 재연결 해주면 된다.

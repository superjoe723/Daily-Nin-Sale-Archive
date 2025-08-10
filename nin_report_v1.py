import pandas as pd
from pytz import timezone
from datetime import datetime, timedelta
import os

# 현재 날짜와 하루 전 날짜 생성
current_date = datetime.now(timezone('Asia/Seoul'))
yesterday_date = current_date - timedelta(days=1)

# 파일명에 사용할 날짜 형식 (yymmdd)
current_date_str = current_date.strftime("%y%m%d")
yesterday_date_str = yesterday_date.strftime("%y%m%d")

# 파일 경로 설정
file1_path = f"crawling_results/nintendo_sale_{yesterday_date_str}.csv"
file2_path = f"crawling_results/nintendo_sale_{current_date_str}.csv"
output_path = f"report_results/report_{current_date_str}.csv"

# CSV 파일 읽기
try:
    df1 = pd.read_csv(file1_path)
    df2 = pd.read_csv(file2_path)
except FileNotFoundError as e:
    print(f"Error: File not found - {e}")
    exit(1)

# 게임 이름 컬럼이 'game name'이라고 가정
# 실제 컬럼 이름이 다를 경우 수정 필요
game_col = 'Game Name'

# 게임 이름 리스트 추출
games_yesterday = set(df1[game_col].dropna())
games_today = set(df2[game_col].dropna())

# 새로 추가된 게임과 삭제된 게임 계산
added_games = games_today - games_yesterday
removed_games = games_yesterday - games_today

# 결과 데이터프레임 생성
report_data = []

# 추가된 게임 정보 추출
for game in added_games:
    game_info = df2[df2[game_col] == game].copy()
    game_info['status'] = 'added'
    report_data.append(game_info)

# 삭제된 게임 정보 추출
for game in removed_games:
    game_info = df1[df1[game_col] == game].copy()
    game_info['status'] = 'removed'
    report_data.append(game_info)

# 데이터프레임 병합
if report_data:
    report_df = pd.concat(report_data, ignore_index=True)
    # 컬럼 순서 조정: 'status'를 첫 번째 컬럼으로
    cols = ['status'] + [col for col in report_df.columns if col != 'status']
    report_df = report_df[cols]
else:
    # 변화가 없을 경우 빈 데이터프레임 생성
    report_df = pd.DataFrame(columns=['status'] + list(df1.columns))

# 결과 CSV 파일로 저장
report_df.to_csv(output_path, index=False)
print(f"Report saved to {output_path}")
if report_df.empty:
    print("No changes detected. Empty report generated.")
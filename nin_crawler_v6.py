import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
import time

# 판매 페이지의 기본 URL
base_url = "https://store.nintendo.co.kr/digital/sale?product_list_order=position&product_list_dir=asc"

# 다운로드 폴더 경로
download_folder = "crawling_results"

# 한 페이지에서 게임 이름, 정가, 할인가, 할인률, 종료 날짜, 페이지 링크를 추출하는 함수
def scrape_page(soup):
    games = []
    # 실제 HTML 구조에 맞춘 클래스 이름
    game_elements = soup.find_all("div", class_="product details category-product-item-info product-item-details")
    if not game_elements:
        print("게임 요소를 찾을 수 없습니다. HTML 구조를 확인하세요.")

    # 현재 날짜 (YYYY-MM-DD 형식)
    current_date = datetime.now().strftime("%Y-%m-%d")

    for game in game_elements:
        try:
            # 게임 이름
            name_elem = game.find("strong", class_="product name product-item-name")
            name = name_elem.text.strip() if name_elem else "이름 없음"

            # 정가
            original_price_elem = game.find("span", class_="old-price")
            original_price = ''.join(filter(str.isdigit, original_price_elem.text.strip())) if original_price_elem else "정가 없음"

            # 할인가
            sale_price_elem = game.find("span", class_="special-price")
            sale_price = ''.join(filter(str.isdigit, sale_price_elem.text.strip())) if sale_price_elem else "할인가 없음"

            # 할인률 계산
            if original_price != "정가 없음" and sale_price != "할인가 없음":
                try:
                    original_price_num = float(original_price)
                    sale_price_num = float(sale_price)
                    sale_rate = (1 - (sale_price_num / original_price_num)) * 100
                    sale_rate = f"{sale_rate:.0f}%"  # 소수점 0째 자리로 포맷
                except (ValueError, ZeroDivisionError):
                    sale_rate = "계산 불가"
            else:
                sale_rate = "계산 불가"

            # 페이지 링크 추출
            link_elem = game.find("a", class_="product-item-link")
            page_link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else "링크 없음"

            # 종료 날짜 추출 (수정된 부분)
            end_date = "종료 날짜 없음"
            if page_link != "링크 없음":
                try:
                    # 개별 게임 페이지 요청
                    import random
time.sleep(random.uniform(1, 3))  # 1~3초 사이 랜덤 딜레이
                    game_response = requests.get(page_link)
                    game_response.raise_for_status()
                    game_soup = BeautifulSoup(game_response.content, "html.parser")
                    end_date_elem = game_soup.find("span", class_="special-period-end")
                    end_date = end_date_elem.text.strip() if end_date_elem else "종료 날짜 없음"
                except requests.RequestException as e:
                    print(f"게임 페이지 요청 중 오류 ({page_link}): {e}")
                    end_date = "요청 오류"

            # 데이터 추가 (종료 날짜 포함)
            games.append((name, original_price, sale_price, sale_rate, current_date, end_date, page_link))
            print(f"추출됨: {name}, 정가: {original_price}, 할인가: {sale_price}, 할인률: {sale_rate}, 날짜: {current_date}, 종료 날짜: {end_date}, 링크: {page_link}")
        except AttributeError as e:
            print(f"데이터 추출 중 오류: {e}")
            continue

    return games

# 메인 함수
def main():
    all_games = []
    page_url = base_url

    # 페이지네이션을 처리하며 데이터 수집
    while True:
        try:
            response = requests.get(page_url)
            response.raise_for_status()  # 요청 실패 시 예외 발생
            soup = BeautifulSoup(response.content, "html.parser")
            games = scrape_page(soup)
            all_games.extend(games)

            # 다음 페이지 링크 찾기
            next_link = soup.find("a", class_="action next")
            if next_link and 'href' in next_link.attrs:
                page_url = next_link['href']
                if not page_url.startswith("http"):
                    page_url = "https://store.nintendo.co.kr" + page_url
                print(f"다음 페이지로 이동: {page_url}")
            else:
                print("마지막 페이지입니다.")
                break
        except requests.RequestException as e:
            print(f"페이지 요청 중 오류: {e}")
            break

    # 데이터가 비어 있는지 확인
    if not all_games:
        print("추출된 게임 데이터가 없습니다. 선택자 또는 페이지 로드를 확인하세요.")
        return

    # crawling_results 폴더가 없으면 생성
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        print(f"폴더 생성됨: {download_folder}")

    # 현재 날짜를 YYMMDD 형식으로 가져오기 (파일명용)
    date_str = datetime.now().strftime("%y%m%d")
    # 파일명 생성
    filename = f"nintendo_sale_{date_str}.csv"
    # 전체 경로 설정
    full_path = os.path.join(download_folder, filename)

    # CSV 파일로 저장
    try:
        with open(full_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            # 헤더에 End Date 추가 (수정된 부분)
            writer.writerow(["Game Name", "Original Price", "Sale Price", "Sale Rate", "Date", "End Date", "Page Link"])
            for game in all_games:
                writer.writerow(game)  # 데이터 작성
        print(f"데이터가 {full_path}에 저장되었습니다.")
    except PermissionError:
        print(f"파일 저장 권한 오류: {full_path}에 접근할 수 없습니다. 권한을 확인하세요.")
    except Exception as e:
        print(f"파일 저장 중 오류: {e}")

if __name__ == "__main__":
    main()
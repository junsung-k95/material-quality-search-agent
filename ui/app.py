"""Streamlit UI for the Material Quality Search Agent."""
import os

import streamlit as st
import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="자재 품질 검색 에이전트", page_icon="🔎", layout="wide")
st.title("🔎 자재 품질 검색 에이전트")

query = st.text_input(
    "품질 문제를 입력하세요",
    placeholder="예: 대시보드 쪽에서 기포가 생김",
)

search_clicked = st.button("검색", type="primary")

if search_clicked and query.strip():
    with st.spinner("검색 중..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/search",
                json={"query": query},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError:
            st.error("서버에 연결할 수 없습니다. API 서버가 실행 중인지 확인하세요.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("요청 시간이 초과되었습니다. 다시 시도해 주세요.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"오류가 발생했습니다: {e.response.text}")
            st.stop()

    # AI 해석 결과
    st.markdown("---")
    st.header("🔍 AI 해석 결과")

    qi = data.get("query_interpretation", {})
    input_terms = qi.get("input_terms", [])
    mapped_component = qi.get("mapped_component", "")
    reason = qi.get("reason", "")
    fallback_used = qi.get("fallback_used", False)

    st.table(
        {
            "입력 단어": [", ".join(input_terms) if input_terms else "-"],
            "매핑 부품": [mapped_component or "-"],
            "이유": [reason or "-"],
        }
    )

    if mapped_component:
        st.info(f"📌 적용 필터: component = {mapped_component}")

    if fallback_used:
        st.warning("⚠️ 조건 완화 검색 적용됨")

    # 검색 결과
    st.markdown("---")
    st.header("📋 검색 결과")

    results = data.get("results", [])
    if not results:
        st.info("검색 결과가 없습니다.")
    else:
        for r in results:
            score_pct = round(r["score"] * 100, 1)
            with st.expander(f"#{r['rank']} — {r['issue']} ({score_pct}%)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**부품**: {r['component']}")
                    st.markdown(f"**문제**: {r['issue']}")
                    st.markdown(f"**원인**: {r['cause']}")
                    st.markdown(f"**해결 방안**: {r['solution']}")
                with col2:
                    st.markdown(f"**MAT코드**: {r['material_code']}")
                    st.markdown(f"**자재 분류**: {r['material_class']}")
                    st.markdown(f"**계층 구조**: {r['class_hierarchy']}")

                sb = r.get("similarity_breakdown", {})
                st.markdown("**유사도 분석**")
                m1, m2, m3 = st.columns(3)
                m1.metric("동일 부품", "✅" if sb.get("same_component") else "❌")
                m2.metric("문제 유사도", f"{sb.get('issue_similarity', 0.0):.3f}")
                m3.metric("원인 유사도", f"{sb.get('cause_similarity', 0.0):.3f}")

    # AI 설명
    explanation = data.get("explanation", "")
    if explanation:
        st.markdown("---")
        st.header("💡 AI 설명")
        st.write(explanation)

elif search_clicked and not query.strip():
    st.warning("검색어를 입력해 주세요.")

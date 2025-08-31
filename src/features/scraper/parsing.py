import logging
import re
from typing import Optional, List
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

try:
    from ...data_models import ScrapedTweet
except Exception:  # pragma: no cover - fallback when running directly
    from src.data_models import ScrapedTweet  # type: ignore

from .selectors import (
    THREAD_INDICATORS,
    X_USER_NAME_XPATH,
    X_USER_HANDLE_XPATH,
    X_TWEET_TEXT_XPATH,
    X_STATUS_LINK_XPATH,
    X_TIME_TAG,
    X_ENGAGEMENT_BUTTON_XPATH,
    X_ANALYTICS_VIEW_XPATH,
    X_HASHTAG_LINKS_XPATH,
    X_MENTION_LINKS_XPATH,
    X_PROFILE_IMG_XPATH,
    X_MEDIA_XPATH,
    X_VERIFIED_ICON_SVG,
)


def _parse_int_from_text(text: str) -> int:
    if not text:
        return 0
    text = text.strip()
    try:
        if "K" in text:
            return int(float(text.replace("K", "")) * 1000)
        if "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        return int(text)
    except Exception:
        return 0


def _get_count(card_element: WebElement, testid: str) -> int:
    try:
        element = card_element.find_element(
            By.XPATH, f".{X_ENGAGEMENT_BUTTON_XPATH.format(testid=testid)}"
        )
        return _parse_int_from_text(element.text)
    except (NoSuchElementException, StaleElementReferenceException):
        return 0


def parse_tweet_card(card_element: WebElement, logger: logging.Logger) -> Optional[ScrapedTweet]:
    try:
        user_name = None
        try:
            user_name_element = card_element.find_element(By.XPATH, f".{X_USER_NAME_XPATH}")
            user_name = user_name_element.text if user_name_element else None
        except NoSuchElementException:
            pass

        user_handle = None
        try:
            user_handle_element = card_element.find_element(By.XPATH, f".{X_USER_HANDLE_XPATH}")
            user_handle = user_handle_element.text if user_handle_element else None
        except NoSuchElementException:
            pass

        tweet_text_parts: List[str] = []
        text_elements = card_element.find_elements(By.XPATH, f".{X_TWEET_TEXT_XPATH}")
        for el in text_elements:
            try:
                tweet_text_parts.append(el.text)
            except StaleElementReferenceException:
                logger.warning("Stale element reference when extracting tweet text part.")
                continue
        text_content = "".join(tweet_text_parts).strip()
        if not text_content:
            return None

        tweet_id = None
        tweet_url = None
        try:
            link_element = card_element.find_element(By.XPATH, f".{X_STATUS_LINK_XPATH}")
            href = link_element.get_attribute("href")
            if href and "/status/" in href:
                tweet_url = href
                tweet_id = href.split("/status/")[-1].split("?")[0]
        except NoSuchElementException:
            logger.warning("Could not find tweet link/ID element for a card.")
            return None

        created_at_dt = None
        try:
            time_element = card_element.find_element(By.XPATH, X_TIME_TAG)
            datetime_str = time_element.get_attribute("datetime")
            if datetime_str:
                created_at_dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except NoSuchElementException:
            logger.debug(f"Timestamp not found for tweet ID {tweet_id}")

        reply_count = _get_count(card_element, "reply")
        retweet_count = _get_count(card_element, "retweet")
        like_count = _get_count(card_element, "like")

        view_count = 0
        try:
            view_element = card_element.find_element(By.XPATH, f".{X_ANALYTICS_VIEW_XPATH}")
            view_count = _parse_int_from_text(view_element.text)
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        tags = [tag.text for tag in card_element.find_elements(By.XPATH, f".{X_HASHTAG_LINKS_XPATH}")]
        mentions = [
            mention.text for mention in card_element.find_elements(By.XPATH, f".{X_MENTION_LINKS_XPATH}")
        ]

        profile_image_url = None
        try:
            img_element = card_element.find_element(By.XPATH, f".{X_PROFILE_IMG_XPATH}")
            profile_image_url = img_element.get_attribute("src")
        except NoSuchElementException:
            pass

        embedded_media_urls: List[str] = []
        media_elements = card_element.find_elements(By.XPATH, f".{X_MEDIA_XPATH}")
        for media_el in media_elements:
            src = media_el.get_attribute("src") or media_el.get_attribute("poster")
            if src:
                embedded_media_urls.append(src)

        is_verified = False
        try:
            card_element.find_element(By.XPATH, f".{X_VERIFIED_ICON_SVG}")
            is_verified = True
        except NoSuchElementException:
            pass

        is_thread_candidate = False
        for indicator in THREAD_INDICATORS:
            if re.search(indicator, text_content, re.IGNORECASE):
                is_thread_candidate = True
                break
        # Heuristic around self-replies omitted (uncertain without reliable selector)

        return ScrapedTweet(
            tweet_id=tweet_id,
            user_name=user_name,
            user_handle=user_handle,
            user_is_verified=is_verified,
            created_at=created_at_dt,
            text_content=text_content,
            reply_count=reply_count,
            retweet_count=retweet_count,
            like_count=like_count,
            view_count=view_count,
            tags=tags,
            mentions=mentions,
            tweet_url=tweet_url,
            profile_image_url=profile_image_url,
            embedded_media_urls=list(set(embedded_media_urls)),
            is_thread_candidate=is_thread_candidate,
        )

    except Exception as e:  # Catch-all to avoid breaking the loop
        logger.error(f"Error parsing tweet card: {e}", exc_info=True)
        return None

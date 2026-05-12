#!/usr/bin/env python3
"""Process Meta Ads data and generate dashboard-data.json."""

import json
import re
from datetime import datetime

INPUT_FILE = "/Users/galyaacobi/.claude/projects/-Users-galyaacobi-Desktop-Obsidian-Vaults--claude-worktrees-sharp-chebyshev-a743f1/1a2aefff-e9dc-42a5-b872-0ca9ee688ce2/tool-results/mcp-32a58151-66b0-49a6-858e-8e2c06f341aa-ads_get_ad_entities-1778595900620.txt"
OUTPUT_FILE = "/Users/galyaacobi/Desktop/Obsidian Vaults/.claude/worktrees/sharp-chebyshev-a743f1/dashboard-data.json"

COMPETITION_PARTICIPANTS = ["K", "BAR", "GAL", "YAIR", "EGZON"]


def parse_number(val):
    """Parse a formatted number string, return 0 if not available."""
    if not val or val == "Not available":
        return 0
    return int(val.replace(",", ""))


def parse_spend(val):
    """Parse '$85,022.86 USD' format to float."""
    if not val or val == "Not available":
        return 0.0
    cleaned = val.replace("$", "").replace(" ", " ").replace("USD", "").replace(",", "").strip()
    return float(cleaned)


def extract_creator(name):
    """Extract creator from ad name."""
    # Check for Vid_K or Video_K pattern anywhere in name (before or without parens)
    if re.match(r'^Vid_K', name, re.IGNORECASE) or re.match(r'^Video_K', name, re.IGNORECASE):
        return "K"

    if "(" not in name:
        # No parenthesis - check for known patterns
        upper = name.upper()
        # Check if name starts with a known creator
        for p in COMPETITION_PARTICIPANTS:
            if upper.startswith(p + "-") or upper.startswith(p + "_") or upper.startswith(p + " ") or upper == p:
                return p
        # Names like "Vid | K95 V2"
        if re.search(r'\bK\d', upper):
            return "K"
        return "OTHER"

    prefix = name.split("(")[0].strip().upper()

    if not prefix:
        return "OTHER"

    # Check if prefix starts with a digit
    if prefix[0].isdigit():
        return "OTHER"

    # Vid_K or Video_K patterns
    if prefix.startswith("VID_K") or prefix.startswith("VIDEO_K"):
        return "K"

    # DCT | K -> K
    if prefix == "DCT | K":
        return "K"

    # GAL K -> GAL
    if prefix.startswith("GAL"):
        return "GAL"

    # K67 -> K, k -> K
    if prefix == "K" or prefix.startswith("K") and (len(prefix) == 1 or prefix[1:].isdigit()):
        return "K"

    # Stat_BAR, Stat_Bar -> BAR
    if prefix.startswith("STAT_BAR"):
        return "BAR"
    if prefix.startswith("BAR"):
        return "BAR"

    # NOAM, NOAMNOAM, Noam, Noam_ -> NOAM (not in competition but still tracked)
    if prefix.startswith("NOAM") or prefix.startswith("NOAM_"):
        return "NOAM"

    # V1 | Ai, V2 | Ai etc -> AI
    if re.match(r'^V\d+ \| AI', prefix):
        return "AI"
    if prefix == "AI":
        return "AI"

    # Men Landing -> OTHER
    if prefix.startswith("MEN ") or prefix.startswith("FATHER"):
        return "OTHER"

    # Clean trailing underscores/spaces
    prefix = prefix.rstrip("_ ")

    # Map common variations
    mappings = {
        "OMER": "OMER",
        "DM": "DM",
        "D": "D",
        "G": "GAL",
        "DANIEL": "DANIEL",
    }

    if prefix in mappings:
        return mappings[prefix]

    return prefix


def main():
    with open(INPUT_FILE) as f:
        raw = json.load(f)

    ads_raw = json.loads(raw["ad_entities"])
    total_count = raw["summary"]["total_count"]

    ads = []
    for ad in ads_raw:
        spend = parse_spend(ad["amount_spent"])
        impressions = parse_number(ad["impressions"])
        three_sec = parse_number(ad["3_second_video_plays"])
        thruplay = parse_number(ad["video_thruplay_watched_actions"])

        hook_rate = (three_sec / impressions * 100) if impressions > 0 else 0.0
        hold_rate = (thruplay / three_sec * 100) if three_sec > 0 else 0.0

        if spend >= 10000:
            tier = "superstar"
        elif spend >= 2500:
            tier = "winner"
        elif spend >= 1000:
            tier = "rising"
        else:
            tier = "testing"

        creator = extract_creator(ad["name"])

        ads.append({
            "id": ad["id"],
            "name": ad["name"],
            "creator": creator,
            "spend": round(spend, 2),
            "impressions": impressions,
            "three_sec_plays": three_sec,
            "thruplay": thruplay,
            "hook_rate": round(hook_rate, 2),
            "hold_rate": round(hold_rate, 2),
            "tier": tier,
        })

    # Sort by spend descending
    ads.sort(key=lambda x: x["spend"], reverse=True)

    # Account-level averages
    all_spends = [a["spend"] for a in ads]
    avg_spend = sum(all_spends) / len(all_spends) if all_spends else 0

    hook_rates = [a["hook_rate"] for a in ads if a["impressions"] > 0]
    avg_hook_rate = sum(hook_rates) / len(hook_rates) if hook_rates else 0

    hold_rates = [a["hold_rate"] for a in ads if a["three_sec_plays"] > 0]
    avg_hold_rate = sum(hold_rates) / len(hold_rates) if hold_rates else 0

    # Leaderboard
    leaderboard = {}
    for p in COMPETITION_PARTICIPANTS:
        p_ads = [a for a in ads if a["creator"] == p]
        winners = [a for a in p_ads if a["tier"] == "winner"]
        superstars = [a for a in p_ads if a["tier"] == "superstar"]
        bonus = len(winners) * 500 + len(superstars) * 1000

        leaderboard[p] = {
            "total_spend": round(sum(a["spend"] for a in p_ads), 2),
            "num_ads": len(p_ads),
            "winners": len(winners),
            "superstars": len(superstars),
            "bonus": bonus,
        }

    output = {
        "last_updated": datetime.now().isoformat(),
        "campaign": "Testing CBO | WOMEN | SALES | 7DC1DV | GIFTING",
        "account_averages": {
            "avg_spend": round(avg_spend, 2),
            "avg_hook_rate": round(avg_hook_rate, 2),
            "avg_hold_rate": round(avg_hold_rate, 2),
        },
        "competition_participants": COMPETITION_PARTICIPANTS,
        "ads": ads,
        "leaderboard": leaderboard,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"Total ads processed: {len(ads)} (reported: {total_count})")
    print(f"\nAccount Averages:")
    print(f"  Avg spend: ${avg_spend:,.2f}")
    print(f"  Avg hook rate: {avg_hook_rate:.2f}%")
    print(f"  Avg hold rate: {avg_hold_rate:.2f}%")
    print(f"\nLeaderboard:")
    for p in COMPETITION_PARTICIPANTS:
        lb = leaderboard[p]
        print(f"  {p}: {lb['num_ads']} ads, ${lb['total_spend']:,.2f} spend, "
              f"{lb['winners']} winners, {lb['superstars']} superstars, ${lb['bonus']:,} bonus")

    # Show creator distribution
    from collections import Counter
    creator_counts = Counter(a["creator"] for a in ads)
    print(f"\nAll creators: {dict(creator_counts.most_common())}")


if __name__ == "__main__":
    main()

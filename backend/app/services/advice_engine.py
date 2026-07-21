from pathlib import Path

import yaml

from app.schemas.product import ProductOut, UserProfile, WarningOut, WarningSeverity
from app.services.nlg import (
    MESSAGES,
    POSITIVE_MESSAGES,
    SUMMARY_TEMPLATES,
    SUMMARY_TEMPLATES_NO_WARNINGS,
)
from app.services.nlg_render import render_template


RULES_PATH = Path(__file__).parent.parent / "rules" / "rules.yaml"

SEVERITY_ORDER = {
    WarningSeverity.DANGER: 0,
    WarningSeverity.WARNING: 1,
    WarningSeverity.CAUTION: 2,
    WarningSeverity.INFO: 3,
}


def load_rules() -> list[dict]:
    with open(RULES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_nutrient(nutrients: dict[str, float], key: str) -> float | None:
    return nutrients.get(key)


def _compare(value: float | None, op: str, target) -> bool:
    if value is None:
        return False
    if op == "gt":
        return value > target
    if op == "lt":
        return value < target
    if op == "eq":
        return value == target
    if op == "gte":
        return value >= target
    if op == "lte":
        return value <= target
    return False


def _check_list_match(profile_values: list, rule_values: list) -> bool:
    profile_set = {v.value if hasattr(v, "value") else v for v in profile_values}
    rule_set = set(rule_values)
    return bool(profile_set & rule_set)


def _check_ingredients_contain(product: ProductOut, keywords: list[str]) -> bool:
    text = (product.ingredients_text or "").lower()
    text += " " + " ".join(i.name.lower() for i in product.ingredients)
    return any(kw.lower() in text for kw in keywords)


def _check_additives_contain(product: ProductOut, e_numbers: list[str]) -> bool:
    product_e = {a.e_number.upper() for a in product.additives}
    return any(e.upper() in product_e for e in e_numbers)


def _check_allergen_match(product: ProductOut, profile_allergens: list[str]) -> tuple[bool, list[str]]:
    if not profile_allergens:
        return False, []
    product_text = (product.allergens or "").lower() + " " + (product.ingredients_text or "").lower()
    matched = []
    for allergen in profile_allergens:
        if allergen.lower() in product_text:
            matched.append(allergen)
    return bool(matched), matched


def _evaluate_condition(key: str, condition, product: ProductOut, profile: UserProfile, nutrients: dict) -> bool:
    if key.startswith("nutrient."):
        nutrient_key = key.split(".", 1)[1]
        val = _get_nutrient(nutrients, nutrient_key)
        if isinstance(condition, dict):
            for op, target in condition.items():
                return _compare(val, op, target)
        return False

    if key == "profile.conditions":
        return _check_list_match(profile.conditions, condition)

    if key == "profile.goals":
        return _check_list_match(profile.goals, condition)

    if key == "profile.age_group":
        age = profile.age_group.value if hasattr(profile.age_group, "value") else profile.age_group
        return age in condition

    if key == "profile.allergens":
        if condition.get("not_empty"):
            return bool(profile.allergens)
        return False

    if key == "product.nova_group":
        if product.nova_group is None:
            return False
        if isinstance(condition, dict):
            for op, target in condition.items():
                return _compare(float(product.nova_group), op, float(target))
        return False

    if key == "product.nutri_score":
        if not product.nutri_score:
            return False
        return product.nutri_score.lower() in [s.lower() for s in condition]

    if key == "ingredients.contains":
        return _check_ingredients_contain(product, condition)

    if key == "additives.contains":
        return _check_additives_contain(product, condition)

    if key == "allergens.match":
        matched, _ = _check_allergen_match(product, profile.allergens)
        return matched

    return False


def evaluate_rules(product: ProductOut, profile: UserProfile, nutrients: dict) -> tuple[list[dict], list[dict], int]:
    rules = load_rules()
    warnings = []
    positives = []
    score = 70

    context = {
        "name": product.name,
        "nutri_score": product.nutri_score or "",
        **{k: nutrients.get(k, 0) for k in nutrients},
    }

    for rule in rules:
        conditions = rule.get("conditions", {})
        all_match = True
        for key, condition in conditions.items():
            if not _evaluate_condition(key, condition, product, profile, nutrients):
                all_match = False
                break

        if not all_match:
            continue

        impact = rule.get("score_impact", 0)
        score += impact

        message_key = rule.get("message_key", rule["id"])
        extra_context = dict(context)

        if message_key == "allergen.match":
            _, matched = _check_allergen_match(product, profile.allergens)
            extra_context["matched_allergens"] = ", ".join(matched)

        message = render_template(MESSAGES.get(message_key, "{{ name }}"), extra_context)

        if rule.get("positive"):
            positives.append({"rule_id": rule["id"], "message_key": message_key, "context": extra_context})
        else:
            warnings.append(
                {
                    "rule_id": rule["id"],
                    "severity": rule.get("severity", "info"),
                    "title": rule.get("title", rule["id"]),
                    "message": message,
                    "evidence": rule.get("evidence"),
                }
            )

    score = max(0, min(100, score))
    return warnings, positives, score


def score_to_label(score: int, has_danger: bool) -> tuple[str, str]:
    if has_danger or score < 30:
        return "danger", "Nguy hiểm"
    if score < 50:
        return "poor", "Không phù hợp"
    if score < 70:
        return "moderate", "Trung bình"
    if score < 85:
        return "good", "Khá phù hợp"
    return "excellent", "Rất phù hợp"


class AdviceEngine:
    def evaluate(self, product: ProductOut, profile: UserProfile, nutrients: dict) -> dict:
        warnings_raw, positives_raw, score = evaluate_rules(product, profile, nutrients)

        severity_map = {
            "danger": WarningSeverity.DANGER,
            "warning": WarningSeverity.WARNING,
            "caution": WarningSeverity.CAUTION,
            "info": WarningSeverity.INFO,
        }

        warnings = [
            WarningOut(
                rule_id=w["rule_id"],
                severity=severity_map.get(w["severity"], WarningSeverity.INFO),
                title=w["title"],
                message=w["message"],
                evidence=w.get("evidence"),
            )
            for w in warnings_raw
        ]
        warnings.sort(key=lambda w: SEVERITY_ORDER.get(w.severity, 99))

        has_danger = any(w.severity == WarningSeverity.DANGER for w in warnings)
        summary_key, suitability_label = score_to_label(score, has_danger)

        context = {"name": product.name, "score": score}
        summary_templates = SUMMARY_TEMPLATES if warnings else SUMMARY_TEMPLATES_NO_WARNINGS
        summary = render_template(summary_templates[summary_key], context)

        positives = []
        for p in positives_raw:
            msg = render_template(POSITIVE_MESSAGES.get(p["message_key"], ""), p["context"])
            if msg:
                positives.append(msg)

        return {
            "suitability_score": score,
            "suitability_label": suitability_label,
            "summary": summary,
            "warnings": warnings,
            "positives": positives,
        }

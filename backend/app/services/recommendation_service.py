from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import RecommendationItem, RecommendationsOut, UserProfile
from app.services.advice_engine import AdviceEngine, score_to_label
from app.services.product_lookup import ProductLookupService, _product_to_schema
from app.schemas.product import WarningSeverity

AGE_LABELS = {
    "newborn": "trẻ sơ sinh (0-12 tháng)",
    "age_1_2": "trẻ 1-2 tuổi",
    "age_2_4": "trẻ 2-4 tuổi",
    "age_4_6": "trẻ 4-6 tuổi",
    "age_6_12": "trẻ 6-12 tuổi",
    "teen": "thanh thiếu niên",
    "adult": "người trưởng thành",
    "elderly": "người cao tuổi",
    "pregnant": "phụ nữ mang thai/cho con bú",
}


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.lookup = ProductLookupService(db)
        self.engine = AdviceEngine()

    def _profile_note(self, profile: UserProfile) -> str:
        age = profile.age_group.value if hasattr(profile.age_group, "value") else profile.age_group
        parts = [f"Gợi ý cho {AGE_LABELS.get(age, age)}"]
        if profile.conditions:
            parts.append(f"bệnh lý: {', '.join(c.value if hasattr(c, 'value') else c for c in profile.conditions)}")
        if profile.goals:
            parts.append(f"mục tiêu: {', '.join(g.value if hasattr(g, 'value') else g for g in profile.goals)}")
        return " · ".join(parts)

    def recommend(
        self,
        profile: UserProfile,
        limit: int = 20,
        min_score: int = 70,
        category: str | None = None,
    ) -> RecommendationsOut:
        query = self.db.query(Product)
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))

        products = query.all()
        scored: list[tuple[int, RecommendationItem, bool]] = []

        for product in products:
            schema = _product_to_schema(product)
            nutrients = self.lookup.get_nutrient_map(schema)
            result = self.engine.evaluate(schema, profile, nutrients)

            has_danger = any(w.severity == WarningSeverity.DANGER for w in result["warnings"])
            if has_danger:
                continue

            score = result["suitability_score"]
            if score < min_score:
                continue

            highlight = result["positives"][0] if result["positives"] else None
            _, label = score_to_label(score, False)

            item = RecommendationItem(
                barcode=product.barcode,
                product_name=product.name,
                brand=product.brand,
                category=product.category,
                source=product.source,
                nutri_score=product.nutri_score,
                nova_group=product.nova_group,
                suitability_score=score,
                suitability_label=label,
                highlight=highlight,
            )
            scored.append((score, item, product.nova_group == 1 or product.nutri_score in ("a", "b")))

        # Prefer higher score, then nutri-score/nova quality
        scored.sort(key=lambda x: (x[0], x[2]), reverse=True)
        recommendations = [item for _, item, _ in scored[:limit]]

        return RecommendationsOut(
            total_evaluated=len(products),
            recommendations=recommendations,
            profile_note=self._profile_note(profile),
        )

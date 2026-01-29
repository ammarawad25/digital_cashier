from src.models.enums import IssueType
from src.models.schemas import PolicyResolution
from typing import Optional

class PolicyEngine:
    def __init__(self, max_auto_refund: float = 50.0):
        self.max_auto_refund = max_auto_refund
    
    def resolve(
        self,
        issue_type: IssueType,
        order_total: float = 0,
        delay_minutes: int = 0
    ) -> PolicyResolution:
        
        if issue_type == IssueType.MISSING_ITEM:
            if order_total <= self.max_auto_refund:
                return PolicyResolution(
                    can_auto_resolve=True,
                    resolution_message=f"استرداد كامل بقيمة {order_total:.2f} SAR تم إصداره للعنصر المفقود",
                    compensation_amount=order_total,
                    requires_escalation=False
                )
            else:
                return PolicyResolution(
                    can_auto_resolve=False,
                    resolution_message="Order value exceeds auto-refund limit, escalating to supervisor",
                    requires_escalation=True
                )
        
        elif issue_type == IssueType.LATE_DELIVERY:
            if delay_minutes > 30:
                credit = min(order_total * 0.2, 25.0)
                return PolicyResolution(
                    can_auto_resolve=True,
                    resolution_message=f"رصيد {credit:.2f} SAR تم إضافته بسبب تأخير التوصيل",
                    compensation_amount=credit,
                    requires_escalation=False
                )
            else:
                return PolicyResolution(
                    can_auto_resolve=True,
                    resolution_message="Delivery is within acceptable range, no compensation required",
                    compensation_amount=0,
                    requires_escalation=False
                )
        
        elif issue_type == IssueType.WRONG_ORDER:
            if order_total <= 75:
                return PolicyResolution(
                    can_auto_resolve=True,
                    resolution_message=f"استرداد كامل بقيمة {order_total:.2f} SAR تم إصداره، مع عرض بديل",
                    compensation_amount=order_total,
                    requires_escalation=False
                )
            else:
                return PolicyResolution(
                    can_auto_resolve=False,
                    resolution_message="High-value order, escalating for manual review",
                    requires_escalation=True
                )
        
        elif issue_type == IssueType.QUALITY:
            if order_total <= 30:
                compensation = order_total * 0.5
                return PolicyResolution(
                    can_auto_resolve=True,
                    resolution_message=f"استرداد 50% بقيمة {compensation:.2f} SAR تم إصداره بسبب مشكلة الجودة",
                    compensation_amount=compensation,
                    requires_escalation=False
                )
            else:
                return PolicyResolution(
                    can_auto_resolve=False,
                    resolution_message="Quality issue requires manager review",
                    requires_escalation=True
                )
        
        else:
            return PolicyResolution(
                can_auto_resolve=False,
                resolution_message="Issue requires manual review",
                requires_escalation=True
            )

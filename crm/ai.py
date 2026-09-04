"""
Thin wrapper around the Anthropic API for the CRM's AI features:
activity summaries, follow-up drafting, next-best-action suggestions, and
the CRM chat assistant.

Requires ANTHROPIC_API_KEY to be set (in .env locally, or as a real
environment variable in production). Get a key at
https://console.anthropic.com/settings/keys — without one, every AI
feature in the CRM degrades gracefully to a clear "not configured" message
instead of crashing.
"""
import os

from django.db.models import Sum

MODEL = 'claude-sonnet-5'

_client = None
_client_checked = False


def get_client():
    """Lazily builds the Anthropic client. Returns None (not an exception)
    if no API key is configured, so callers can show a friendly message."""
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    from anthropic import Anthropic
    _client = Anthropic(api_key=api_key)
    return _client


def ask_claude(system, messages, max_tokens=500):
    """messages: list of {"role": "user"|"assistant", "content": str}.
    Returns (text, error) — exactly one of which is None."""
    client = get_client()
    if client is None:
        return None, ("AI features need an ANTHROPIC_API_KEY. Add it to your .env file "
                       "(see .env.example) — get a key at https://console.anthropic.com/settings/keys")
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        text = ''.join(block.text for block in response.content if hasattr(block, 'text'))
        return text, None
    except Exception as e:
        return None, f"AI request failed: {e}"


# --------------------------------------------------------------- Context builders
# Each of these turns CRM records into a compact plain-text brief for
# Claude — never raw model dumps, so token usage and cost stay small and
# the model isn't distracted by irrelevant fields.

def context_for_contact(contact):
    lines = [
        f"Contact: {contact.full_name}",
        f"Email: {contact.email or '-'} | Phone: {contact.phone or '-'} | Title: {contact.job_title or '-'}",
        f"Company: {contact.company or '-'}",
        f"Lifecycle stage: {contact.get_lifecycle_stage_display()}",
    ]
    deals = list(contact.deals.all()[:10])
    if deals:
        lines.append("Deals:")
        for d in deals:
            lines.append(f"  - {d.name}: ${d.amount} ({d.get_status_display()}, stage: {d.stage})")
    activities = list(contact.activities.order_by('-created_at')[:15])
    if activities:
        lines.append("Recent activity (most recent first):")
        for a in activities:
            lines.append(f"  - [{a.get_activity_type_display()}] {a.created_at:%Y-%m-%d}: {a.content}")
    else:
        lines.append("No activity logged yet.")
    return '\n'.join(lines)


def context_for_deal(deal):
    lines = [
        f"Deal: {deal.name}",
        f"Amount: ${deal.amount} | Stage: {deal.stage} | Status: {deal.get_status_display()}",
        f"Company: {deal.company or '-'} | Contact: {deal.contact or '-'}",
        f"Close date: {deal.close_date or '-'}",
    ]
    activities = list(deal.activities.order_by('-created_at')[:15])
    if activities:
        lines.append("Recent activity (most recent first):")
        for a in activities:
            lines.append(f"  - [{a.get_activity_type_display()}] {a.created_at:%Y-%m-%d}: {a.content}")
    else:
        lines.append("No activity logged yet.")
    tasks = list(deal.tasks.all()[:10])
    if tasks:
        lines.append("Related tasks:")
        for t in tasks:
            lines.append(f"  - {t.title} (due {t.due_date or '-'}, status: {t.get_status_display()})")
    return '\n'.join(lines)


def context_for_user(user, is_manager_fn):
    """Summarizes the CRM data this user can see, for the chat assistant.
    Respects the same rep-vs-manager visibility as the rest of the CRM."""
    from .models import Deal, Contact, Company, Task

    manager = is_manager_fn(user)
    deals = Deal.objects.all() if manager else Deal.objects.filter(owner=user)
    contacts = Contact.objects.all() if manager else Contact.objects.filter(owner=user)
    companies = Company.objects.all() if manager else Company.objects.filter(owner=user)
    tasks = Task.objects.all() if manager else Task.objects.filter(assigned_to=user)

    open_deals = deals.filter(status='open')
    lines = [
        f"User: {user.username} ({'manager, sees all CRM data' if manager else 'rep, sees only records they own'})",
        f"Contacts: {contacts.count()} | Companies: {companies.count()}",
        f"Open deals: {open_deals.count()} | Open pipeline value: ${open_deals.aggregate(t=Sum('amount'))['t'] or 0}",
        f"Won revenue: ${deals.filter(status='won').aggregate(t=Sum('amount'))['t'] or 0}",
        "",
        "Open deals (up to 25, largest first):",
    ]
    for d in open_deals.order_by('-amount')[:25]:
        lines.append(f"  - {d.name} | ${d.amount} | stage: {d.stage} | company: {d.company or '-'} | close: {d.close_date or '-'}")

    lines.append("")
    lines.append("Incomplete tasks (up to 25, soonest due first):")
    for t in tasks.exclude(status='completed').order_by('due_date')[:25]:
        lines.append(f"  - {t.title} | due {t.due_date or '-'} | priority: {t.priority} | status: {t.status}")

    return '\n'.join(lines)

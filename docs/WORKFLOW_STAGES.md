# LinkedIn Automation Workflow Stages

## Overview
The CRM tracks each contact's position in the LinkedIn outreach workflow. This enables automated LinkedIn engagement sequences managed by an AI agent.

## Workflow Stages

### 1. **new** (Default)
- **Description**: Contact just added to CRM
- **Next Action**: Send connection request
- **Badge Color**: Gray

### 2. **connect_sent**
- **Description**: Connection request sent on LinkedIn
- **Next Action**: Wait for acceptance, or like/comment on posts
- **Badge Color**: Blue

### 3. **connected**
- **Description**: Connection request accepted
- **Next Action**: Like their recent posts
- **Badge Color**: Green

### 4. **liked**
- **Description**: Liked their LinkedIn posts
- **Next Action**: Comment on their posts
- **Badge Color**: Purple

### 5. **commented**
- **Description**: Commented on their LinkedIn posts
- **Next Action**: Send first message
- **Badge Color**: Indigo

### 6. **messaged**
- **Description**: Sent first outreach message
- **Next Action**: Wait for reply, follow up after X days
- **Badge Color**: Yellow

### 7. **replied**
- **Description**: Contact replied to message
- **Next Action**: Continue conversation, qualify lead
- **Badge Color**: Teal

### 8. **qualified**
- **Description**: Qualified as a good lead
- **Next Action**: Schedule call, send proposal
- **Badge Color**: Emerald

### 9. **disqualified**
- **Description**: Not a good fit
- **Next Action**: None (archived)
- **Badge Color**: Red

---

## Database Fields

### `workflow_stage` (VARCHAR 50)
Current stage in the workflow (see stages above)

### `last_action` (VARCHAR 100)
Description of the last action taken
- Examples: "Sent connection request", "Liked 3 posts", "Sent message: Hey John..."

### `last_action_date` (DATETIME)
Timestamp when the last action was performed

### `next_action` (VARCHAR 100)
Description of the next planned action
- Examples: "Like posts", "Send message", "Follow up", "Schedule call"

### `next_action_date` (DATETIME)
Scheduled date/time for the next action

### `automation_notes` (TEXT)
Free-form notes about the automation sequence
- Examples: "Waiting 3 days before follow-up", "Interested in product demo", "Not responding - try different approach"

---

## Example Workflow Sequence

```
Day 1:  new → Send connection request → connect_sent
Day 2:  connect_sent → Connection accepted → connected
Day 3:  connected → Like 3 posts → liked
Day 5:  liked → Comment on post about AI → commented
Day 7:  commented → Send personalized message → messaged
Day 10: messaged → Received reply → replied
Day 12: replied → Qualified as good fit → qualified
```

---

## Future: AI Agent Integration

The AI agent will:
1. **Monitor** contacts in each stage
2. **Execute** actions when `next_action_date` is reached
3. **Update** workflow stage after each action
4. **Personalize** messages based on contact's profile, tags, and company
5. **Learn** from successful sequences to optimize timing and messaging

Example agent logic:
```python
# Pseudo-code for AI agent
for contact in get_contacts_due_for_action():
    if contact.workflow_stage == 'new':
        send_connection_request(contact)
        update_contact(
            workflow_stage='connect_sent',
            last_action='Sent connection request',
            last_action_date=now(),
            next_action='Check if accepted',
            next_action_date=now() + 2.days
        )
    elif contact.workflow_stage == 'connected':
        posts = get_recent_posts(contact.linkedin_url)
        like_posts(posts[:3])
        update_contact(
            workflow_stage='liked',
            last_action=f'Liked {len(posts[:3])} posts',
            last_action_date=now(),
            next_action='Comment on post',
            next_action_date=now() + 2.days
        )
    # ... etc
```

---

## CRM Display

The CRM table now shows:
- **Workflow Stage**: Colored badge showing current stage
- **Last Action**: What was done + when
- **Next Action**: What's planned + when

This gives you full visibility into the automation pipeline!


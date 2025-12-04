# Admin Authentication Guide

## Overview

Admin endpoints require **both authentication AND admin authorization**. Not all authenticated users can access admin endpoints.

## How Admin Authentication Works

The `require_admin_role` function checks if a user is an admin using **three methods** (in priority order):

### Method 1: ADMIN_EMAILS Environment Variable (Recommended)
- Set `ADMIN_EMAILS` environment variable with comma-separated admin email addresses
- Example: `ADMIN_EMAILS=admin@example.com,admin2@example.com`
- **Pros**: Simple, no Cognito configuration needed
- **Cons**: Must redeploy to add/remove admins

### Method 2: Cognito Groups
- Add user to "admin" group in Cognito User Pool
- Token will include `cognito:groups` claim with `["admin"]`
- **Pros**: Can manage admins via Cognito Console
- **Cons**: Requires Cognito group setup

### Method 3: Custom Token Claims
- Token has `admin: true` or `custom:admin: "true"` claim
- **Pros**: Flexible
- **Cons**: Requires custom token generation

## Current Status

**⚠️ Currently, admin endpoints only require authentication** - any authenticated user can access them.

**After deploying with admin authentication:**
- ✅ Only users who pass admin check can access
- ❌ Non-admin users get `403 Forbidden`
- ❌ Unauthenticated users get `401 Unauthorized`

## Configuration

### Option 1: Use ADMIN_EMAILS (Easiest)

Add to `template.yaml` AdminFunction environment variables:

```yaml
Environment:
  Variables:
    CONVERSATION_LOGS_TABLE_NAME: !Ref ConversationLogsTable
    LOG_LEVEL: INFO
    COGNITO_USER_POOL_ID: !Ref UserPool
    COGNITO_APP_CLIENT_ID: !Ref UserPoolClient
    ADMIN_EMAILS: "admin@example.com,admin2@example.com"  # Add this
```

### Option 2: Use Cognito Groups

1. Go to AWS Cognito Console
2. Select your User Pool
3. Go to **Groups** → **Create group**
4. Create group named `admin`
5. Add users to the `admin` group
6. Users in the group will have `cognito:groups: ["admin"]` in their token

### Option 3: Custom Claims (Advanced)

Requires custom token generation with admin claim. Not recommended for most use cases.

## Testing Admin Access

### Test 1: Non-Admin User (Should Fail)
```bash
# Get token for regular user
TOKEN="<regular-user-token>"

# Try to access admin endpoint
curl -X GET \
  https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations \
  -H "Authorization: Bearer $TOKEN"

# Expected: 403 Forbidden
```

### Test 2: Admin User (Should Succeed)
```bash
# Get token for admin user
TOKEN="<admin-user-token>"

# Access admin endpoint
curl -X GET \
  https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK with conversation list
```

### Test 3: No Authentication (Should Fail)
```bash
# Try without token
curl -X GET \
  https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations

# Expected: 401 Unauthorized
```

## Security Notes

1. **Admin emails are case-sensitive** - `Admin@Example.com` ≠ `admin@example.com`
2. **Token must be valid** - Expired or invalid tokens will return 401
3. **Admin check happens server-side** - Client-side checks are not sufficient
4. **Logs are recorded** - All admin access attempts are logged (success and failure)

## Troubleshooting

### Issue: Getting 403 even though I'm admin
- Check if email is exactly in `ADMIN_EMAILS` (case-sensitive)
- Check if user is in Cognito `admin` group
- Check token claims: Decode JWT and verify `cognito:groups` or `admin` claim

### Issue: Getting 401
- Token might be expired - get a new token
- Token might be invalid - verify token format
- Check if `COGNITO_USER_POOL_ID` and `COGNITO_APP_CLIENT_ID` are correct

### Issue: Everyone can access admin endpoints
- Verify `require_admin_role` is used (not `get_current_user_id`)
- Check if `ADMIN_EMAILS` is set correctly
- Verify Cognito groups are configured

## Example: Setting Up Admin via ADMIN_EMAILS

1. **Add to template.yaml**:
```yaml
AdminFunction:
  Environment:
    Variables:
      ADMIN_EMAILS: "admin@yourdomain.com"
```

2. **Deploy**:
```bash
make deploy
```

3. **Test**:
```bash
# Get admin user token
TOKEN="<admin-user-token>"

# Access admin endpoint
curl -X GET \
  https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/Prod/api/v1/admin/chat/conversations \
  -H "Authorization: Bearer $TOKEN"
```

## Example: Setting Up Admin via Cognito Groups

1. **AWS Console**:
   - Cognito → User Pools → Your Pool → Groups → Create group
   - Name: `admin`
   - Add users to group

2. **Verify in Token**:
   - Decode JWT token
   - Check for `"cognito:groups": ["admin"]` claim

3. **Test**:
   - Use token from user in admin group
   - Access admin endpoints


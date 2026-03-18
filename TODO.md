# Fix Login Redirect to Dashboard for Both Normal Users and Superadmins

## Steps to Complete:

- [ ] Step 1: Add dashboard URL to inventory/urls.py
- [ ] Step 2: Update core/settings.py LOGIN_REDIRECT_URL
- [x] Step 3: Fix redirects in inventory/views.py from 'home' to 'dashboard'\n- [x] Step 4: Rename 'home' URL in core/urls.py to 'landing' for clarity
- [ ] Step 5: Test login for normal approved canteen owner → dashboard (index.html)
- [ ] Step 6: Test login for superadmin → superadmin_dashboard (admin_approval.html)
- [ ] Step 7: Test sale completion redirects back to dashboard
- [ ] Step 8: Complete and verify working for both user types


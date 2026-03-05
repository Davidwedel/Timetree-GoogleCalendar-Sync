# How to Get Your TimeTree Session Cookie

## Step-by-Step Guide

### Chrome / Edge / Brave

1. **Open TimeTree and Log In**
   - Go to https://timetreeapp.com
   - Log into your account

2. **Open Developer Tools**
   - Press `F12` (or `Ctrl+Shift+I` on Windows/Linux, `Cmd+Option+I` on Mac)

3. **Go to Application Tab**
   - Click on the "Application" tab in DevTools
   - If you don't see it, click the `>>` button to find it

4. **Navigate to Cookies**
   - In the left sidebar, expand "Storage" → "Cookies"
   - Click on `https://timetreeapp.com`

5. **Find the Cookie**
   - Look through the list for a cookie named **`_timetree_session`**
   - It should be a long string of characters (not just numbers)
   - Example format: `eyJhbGciOiJIUzI1NiJ9.eyJ...` (much longer)

6. **Copy the Value**
   - Double-click the "Value" column for `_timetree_session`
   - Copy the entire value (it might be very long, 200+ characters)

### Firefox

1. **Open TimeTree and Log In**
   - Go to https://timetreeapp.com
   - Log into your account

2. **Open Developer Tools**
   - Press `F12` (or `Ctrl+Shift+I`)

3. **Go to Storage Tab**
   - Click on the "Storage" tab
   - Expand "Cookies" in the left sidebar
   - Click on `https://timetreeapp.com`

4. **Find and Copy**
   - Look for `_timetree_session` in the Name column
   - Copy the value from the Value column

### Safari

1. **Enable Developer Tools**
   - Safari → Settings → Advanced
   - Check "Show Develop menu in menu bar"

2. **Open TimeTree and Log In**
   - Go to https://timetreeapp.com
   - Log into your account

3. **Open Web Inspector**
   - Develop → Show Web Inspector (or `Cmd+Option+I`)

4. **Go to Storage Tab**
   - Click "Storage" tab
   - Select "Cookies" → `https://timetreeapp.com`

5. **Find and Copy**
   - Look for `_timetree_session`
   - Copy its value

## Alternative Method: Network Tab

If you can't find the cookie in Storage/Application:

1. **Open DevTools** (F12)
2. **Go to Network Tab**
3. **Refresh the page** (F5 or Ctrl+R)
4. **Click on the first request** (usually just "timetreeapp.com")
5. **Look at Request Headers**
   - Scroll down to "Request Headers"
   - Find the "Cookie:" header
   - Look for `_timetree_session=XXXX` in the cookie string
   - Copy everything after `_timetree_session=` up to the next semicolon

## What the Cookie Looks Like

❌ **NOT this** (too short, wrong format):
```
_session_id: 4d0610c906d64780ed2a5a7ea61c3bf2
```

✅ **More like this** (long JWT-like token):
```
_timetree_session: eyJhbGciOiJIUzI1NiJ9.eyJzZXNzaW9uX2lkIjoiNGQwNjEwYzkwNmQ2NDc4MGVkMmE1YTdlYTYxYzNiZjIiLCJ1c2VyX2lkIjoxMjM0NTY3LCJleHAiOjE3MDk1...
```

The value should be **very long** (often 200-500+ characters).

## Common Issues

### "I don't see _timetree_session"
- Make sure you're logged into TimeTree
- Try refreshing the page and looking again
- Check if the cookie has a different but similar name
- TimeTree might use different cookie names for different regions

### "My cookie doesn't work"
- Make sure you copied the entire value (it's very long)
- Don't include quotes or extra spaces
- Make sure you're still logged in (cookies expire)
- Try logging out and back in to get a fresh cookie

### "Cookie stopped working"
- Session cookies expire after some time (hours/days)
- You'll need to get a new one periodically
- Keep your TimeTree login active in the browser

## Security Warning

⚠️ **Keep your session cookie private!**
- Anyone with your session cookie can access your TimeTree account
- Don't share it publicly
- Don't commit it to Git (it's in .gitignore)
- Store it only in your `.env` file

## Still Having Trouble?

Try this alternative approach:
1. Open DevTools → Network tab
2. Navigate to your calendar in TimeTree
3. Look for API requests to `timetreeapp.com/api/`
4. Click on one of them
5. In "Headers" → "Request Headers" → look at the "Cookie" header
6. Find `_timetree_session=...` and copy that value

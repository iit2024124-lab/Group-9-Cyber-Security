const $ = id => document.getElementById(id);
$('show-password').onclick = () => {
  const show = $('password').type === 'password';
  $('password').type = show ? 'text' : 'password';
  $('show-password').textContent = show ? 'Hide' : 'Show';
  $('show-password').setAttribute('aria-label', show ? 'Hide password' : 'Show password');
};
$('login-form').addEventListener('submit', async event => {
  event.preventDefault();
  $('submit').disabled = true;
  $('error').hidden = true;
  try {
    const response = await fetch('/api/login', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: $('username').value, password: $('password').value})
    });
    const data = await response.json();
    if (!response.ok) throw Error('Unable to sign in. Please try again.');
    if (!data.ok) throw Error(data.message);
    $('name').textContent = data.user.name.split(' ')[0];
    $('account-name').textContent = data.user.username;
    $('account-email').textContent = data.user.email;
    $('password').value = '';
    $('login-panel').hidden = true;
    $('profile').hidden = false;
  } catch (error) {
    $('error').textContent = error instanceof TypeError ? 'Unable to connect. Please try again.' : error.message;
    $('error').hidden = false;
  } finally { $('submit').disabled = false; }
});
$('logout').onclick = () => {
  $('profile').hidden = true;
  $('login-panel').hidden = false;
  $('login-form').reset();
  $('password').type = 'password';
  $('show-password').textContent = 'Show';
  $('show-password').setAttribute('aria-label', 'Show password');
  $('error').hidden = true;
  $('username').focus();
};

import React, {useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {api} from '../../api';

export default function Register({onAuth}) {
  const [form,setForm] = useState({username:'',first_name:'',last_name:'',email:'',password:''});
  const [error,setError] = useState('');
  const navigate = useNavigate();
  async function register(event) {
    event.preventDefault(); setError('');
    try {const user = await api('register',{method:'POST',body:JSON.stringify(form)}); onAuth(user); navigate('/dealers');}
    catch (err) {setError(err.message);}
  }
  return <main className="auth-card"><p className="eyebrow">JOIN OUR COMMUNITY</p><h1>Create an account</h1>
    <p>Share your experience and help other drivers choose with confidence.</p>
    <form onSubmit={register}>
      <label>Username<input name="username" autoComplete="username" required value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/></label>
      <div className="form-grid"><label>First Name<input name="first_name" autoComplete="given-name" required value={form.first_name} onChange={e=>setForm({...form,first_name:e.target.value})}/></label>
      <label>Last Name<input name="last_name" autoComplete="family-name" required value={form.last_name} onChange={e=>setForm({...form,last_name:e.target.value})}/></label></div>
      <label>Email<input type="email" name="email" autoComplete="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label>
      <label>Password<input type="password" name="password" autoComplete="new-password" minLength={8} required value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label>
      {error && <p role="alert" className="alert alert-danger">{error}</p>}
      <button className="button primary" type="submit">Register</button>
    </form><p className="mt-3">Already registered? <Link to="/login">Log in</Link></p></main>;
}

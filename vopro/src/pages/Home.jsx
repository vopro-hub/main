import React from 'react';
import { Link } from 'react-router-dom';
import '../static/home.css';
import '../App.css';


const Home = () => {
  return (
    <div className="home-container">
      <div></div>
      <div>
       
        <h1 className="hero-heading">Run Your Business Like a Pro — From Anywhere</h1>
        <section className="hero-section"></section>
        <div className="hero-wraper">
            <div className="hero-content">
            <p>Build your dream business from anywhere with a complete cloud-based office suite.</p>
            <p> <strong>Every day without GenSparq, you’re missing leads, looking unprofessional, and falling behind more organized competitors. </strong></p>
          </div>
          <div className="hero-buttons">
              <Link to="/register" className="cta-btn">Look Like a Pro in 5 Minutes</Link>
              <Link to="/generate" className="cta-btn secondary">Try the Generator</Link>
             
            </div>
          </div>
        
         <section className="how-it-works">
          <h2>Your business is growing — but your tools aren’t.</h2>
          <ol className="steps">
            <li> ❌ Missing client calls when you're in meetings</li>
            <li> ❌ No professional address to build trust</li>
            <li> ❌ Wasting hours on emails and admin tasks</li>
            <li> ❌ Juggling too many tools with no smart assistant</li>
          </ol>
          <p>The result? Lost leads and revenue. Missed opportunities. Burnout.</p>
          <p> <stron> Your next 5 clients are trying to reach you. Will they find a pro — or pass you by?</stron></p>
          <div className="hero-buttons">
            <Link to="/register" className="cta-btn">Stop Losing Clients — Try It Free</Link>
          </div>
        </section>
        <section className="features">
          <h2>What You Get</h2>
          <div className="feature-list">
            <div className="feature-card">
              <h4>Digital Business Address</h4>
              <p>Look professional, register legally, and build trust — without renting an office.</p>
            </div>
            <div className="feature-card">
              <h4>AI Receptionist</h4>
              <p>Never miss a call, message or appointment with 24/7 virtual receptionist support.</p>
            </div>
            <div className="feature-card">
              <h4>AI Office Assistant</h4>
              <p>
                Gain 10 hours back every week — with your AI assistant handling the busywork.
                Chat with your assistant 24/7 to summarize emails, book meetings, auto-reply to inquiries, and more.
                </p>
            </div>
            <div className="feature-card">
              <h4>AI-Powered Content</h4>
              <p>Generate engaging posts tailored to your business with a click.</p>
            </div>
            <div className="feature-card">
              <h4>Smart Scheduling</h4>
              <p>Automated meeting coordination, calendar sync and reminders, and social media posts for peak engagement times.</p>
            </div>
            <div className="feature-card">
              <h4>Campaign Management</h4>
              <p>Organize posts by campaigns and track your marketing goals easily.</p>
            </div>
            <div className="feature-card">
              <h4>Team Collaboration</h4>
              <p>Chat, share files, and manage tasks securely with your team and clients.</p>
            </div>
            <div className="feature-card">
              <h4>Role-Based Access</h4>
              <p>Built for users and suppliers with personalized dashboards.</p>
            </div>
          </div>
        </section>
  
        <section className="how-it-works">
          <h2>Built for You</h2>
          <h4>GenSparq is made for Africa’s new generation of business owners who run big dreams from small rooms.</h4>
          <p> We know the challenges you face — and built a tool to match your hustle.</p>
          <ul className="steps">
            <li>🌐 Affordable plans (no credit card needed)</li>
            <li>📍 Local support teams</li>
            <li>🚀 Scales with you as you grow</li>
          </ul>
          <p>From side hustle to full hustle — GenSparq grows with you.</p>
          <p>GenSparq gives you the tools of a real office — minus the rent.</p>
        </section>
        <section className="how-it-works">
          <h2>How It Works</h2>
          <ol className="steps">
            <li><strong>1. Sign Up</strong> – Create a free account based on your role.</li>
            <li><strong>2. Generate</strong> – Use AI to create powerful post content.</li>
            <li><strong>3. Schedule</strong> – Select dates and let our engine publish automatically.</li>
            <li><strong>4. Manage</strong> – Edit, cancel, or track your posts in the dashboard.</li>
          </ol>
        </section>
        <section id="testimonials" className="testimonials-section">
          <h3>What Our Users Say</h3>
          <div className="testimonials">
            <blockquote>
              “It’s like having a full office team — without the payroll.” <br/> <span>— Kwame, Freelancer (Remote Africa)</span>
            </blockquote>
            <blockquote>
              "CloudOffice helped me scale my remote business with zero overhead. Clients trust me more — and I’ve closed more deals." <br/> <span>- Aisha, Tech Founder (Ghana)</span>
            </blockquote>
            <blockquote>
              "The AI receptionist alone is worth it. I never miss a lead and my clients love the professionalism." <br/> <span>- Tolu, Digital Marketer (Nigeria)</span>
            </blockquote>
          </div>
        </section>
        <section id="faq" className="faq-section">
          <h3>FAQs</h3>
          <div className="faq-list">
            <div className="faq-item">
              <h4>Can I change my plan later?</h4>
              <p>Yes, you can upgrade or downgrade your plan anytime.</p>
            </div>
            <div className="faq-item">
              <h4>Do I need a physical office to use GenSparq?</h4>
              <p>No. GenSparq is 100% virtual.</p>
            </div>
            <div className="faq-item">
              <h4>Is this legal for business registration?</h4>
              <p>Yes. You’ll get a legally compliant address.</p>
            </div>
            <div className="faq-item">
              <h4>Is this only for African entrepreneurs?</h4>
              <p>GenSparq is built for Africa-first founders — but open globally</p>
            </div>
            <div className="faq-item">
              <h4>Do you offer support?</h4>
              <p>Absolutely, we offer chat, email, and phone support based on your plan.</p>
            </div>
          </div>
        </section>
        <section className="call-to-action">
          <h2>Start Simplifying Your Business Today</h2>
          <p>You’re doing it all — but it doesn’t have to be this hard.</p>
          <p>We believe in our platform — and you will too.</p>
          <Link to="/register" className="cta-btn">Join Now</Link>
        </section>
        <section className="demo-section">
          <h2>📺 Watch How VOP Works in 60 Seconds</h2>
          <p>Embed video or animated walkthrough here (or slideshow)</p>
        </section>
        <section id="contact" className="contact-section">
          <h2>Contact Us</h2>
          <p>Have questions? We're here to help: <a href="mailto:support@cloudoffice.com">support@cloudoffice.com</a></p>
        </section>
        <footer className="footer">
          <p>&copy; {new Date().getFullYear()} CloudOffice. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
};

export default Home;

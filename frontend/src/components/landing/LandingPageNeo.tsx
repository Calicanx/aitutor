/**
 * Landing Page Neo: Extreme Neo-Brutalism Style
 * Content from landing-page-content_2.md
 * Mobile-first, visually appealing, interactive with animations
 */
import React, { useEffect, useState } from 'react';
import TeachrLogo from './TeachrLogo';
import './landing.scss';

interface LandingPageNeoProps {
  onGetStarted: () => void;
}

const LandingPageNeo: React.FC<LandingPageNeoProps> = ({ onGetStarted }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    setIsVisible(true);
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="landing-page landing-page-neo">
      {/* Background texture overlay */}
      <div className="neo-bg-texture" />
      
      <div className="landing-container">
        {/* Header with decorative badge */}
        <header className="landing-header neo-header">
          <TeachrLogo size="medium" />
          <div className="neo-badge neo-badge-header" style={{ transform: 'rotate(3deg)' }}>
            NEW
          </div>
        </header>

        {/* Hero Section with extreme styling */}
        <section className="landing-hero neo-hero">
          {/* Decorative floating shapes - positioned behind content */}
          <div className="neo-shape neo-shape-1" />
          <div className="neo-shape neo-shape-2" />
          <div className="neo-shape neo-shape-3" />
          
          <div className="hero-content" style={{ opacity: isVisible ? 1 : 0, transition: 'opacity 0.5s ease-out' }}>
            {/* Badge */}
            <div className="neo-badge neo-badge-hero" style={{ transform: 'rotate(-2deg)' }}>
              ACTUALLY UNDERSTAND
            </div>
            
            <h1 className="hero-title neo-title-stroke">
              What If You Actually Understood It?
            </h1>
            <p className="hero-subtitle">
              Not memorized it for the test. Not faked your way through it. Actually got it. That's what we're building.
            </p>
            <div className="hero-cta-wrapper">
              <button 
                onClick={onGetStarted}
                className="cta-button cta-button-neo neo-button-press"
              >
                Try It Free
              </button>
              <div className="neo-badge neo-badge-cta" style={{ transform: 'rotate(5deg)' }}>
                NO CREDIT CARD
              </div>
            </div>
          </div>
        </section>

        {/* The Real Problem Section */}
        <section className="neo-section neo-section-white" style={{ 
          transform: `translateY(${Math.min(scrollY * 0.1, 50)}px)`,
          transition: 'transform 0.1s ease-out'
        }}>
          <div className="neo-section-header">
            <h2 className="neo-heading-large">The Real Problem</h2>
            <h3 className="neo-heading-medium">You Don't Need More Content.<br />You Need Better Understanding.</h3>
          </div>
          <div className="neo-card neo-card-lifted">
            <p className="neo-text-large">
              The internet has more educational content than any human could consume in ten lifetimes.
            </p>
            <p className="neo-text-body">
              Khan Academy. YouTube. Coursera. Udemy. Brilliant. That random guy with a whiteboard who pronounces "integral" weird.
            </p>
            <p className="neo-text-emphasis">
              You're not struggling because there's not enough out there. You're struggling because none of it was built for you.
            </p>
            <p className="neo-text-body">
              Generic explanations. One-size-fits-all pacing. Videos that assume you understood minute three when you got lost at minute one.
            </p>
            <p className="neo-text-large neo-text-bold">
              More content isn't the answer. Better teaching is.
            </p>
          </div>
        </section>

        {/* The Difference Section - Yellow background with texture */}
        <section className="neo-section neo-section-yellow">
          <div className="neo-section-header">
            <h2 className="neo-heading-large">The Difference</h2>
            <h3 className="neo-heading-medium">Teaching vs. Content</h3>
          </div>
          <div className="neo-comparison-grid">
            <div className="neo-card neo-card-comparison neo-card-red-border" style={{ transform: 'rotate(-1deg)' }}>
              <div className="neo-badge neo-badge-card" style={{ transform: 'rotate(8deg)' }}>
                CONTENT
              </div>
              <h4 className="neo-card-title" style={{ color: '#FF6B6B' }}>Content</h4>
              <p className="neo-text-body">is a video you pause, rewind, pause again, then give up on.</p>
              <p className="neo-text-body">moves at its own pace.</p>
              <p className="neo-text-body">doesn't know if you understood.</p>
            </div>
            <div className="neo-card neo-card-comparison" style={{ transform: 'rotate(1deg)' }}>
              <div className="neo-badge neo-badge-card neo-badge-yellow" style={{ transform: 'rotate(-8deg)' }}>
                TEACHING
              </div>
              <h4 className="neo-card-title">Teaching</h4>
              <p className="neo-text-body">is someone who notices you're confused and tries a different angle.</p>
              <p className="neo-text-body">moves at yours.</p>
              <p className="neo-text-body">checks. And adjusts. And checks again.</p>
            </div>
          </div>
          <p className="neo-statement-large">
            teachr isn't content. It's teaching.
          </p>
        </section>

        {/* What Actually Changes Section */}
        <section className="neo-section neo-section-cream">
          <div className="neo-section-header">
            <h2 className="neo-heading-large">What Actually Changes</h2>
            <h3 className="neo-heading-medium">When Learning Finally Works</h3>
          </div>
          <div className="neo-grid neo-grid-2">
            {[
              {
                title: "You stop avoiding the subject.",
                description: "That class you dread? The homework you leave until last? It's not because you're bad at it. It's because no one's taught you properly yet.",
                rotation: -1
              },
              {
                title: "You build real confidence.",
                description: "Not the fake kind where you hope the test questions are easy. The kind where you walk in knowing you've got this.",
                rotation: 1
              },
              {
                title: "You save time.",
                description: "No more watching 45-minute videos for 3 minutes of relevance. No more hunting through forums for someone who had your exact question. Just direct answers to what you actually need.",
                rotation: -1
              },
              {
                title: "You start to like it.",
                description: "Controversial opinion: most subjects are interesting when you actually understand them. Math isn't boring. Bad teaching is boring.",
                rotation: 1
              }
            ].map((item, idx) => (
              <div
                key={idx}
                className="neo-card neo-card-hover"
                style={{ transform: `rotate(${item.rotation}deg)` }}
              >
                <h4 className="neo-card-title">{item.title}</h4>
                <p className="neo-text-body">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How It Works Section - Violet background */}
        <section className="neo-section neo-section-violet">
          <div className="neo-section-header">
            <h2 className="neo-heading-large">How It Works</h2>
            <h3 className="neo-heading-medium">Simple. Like It Should Be.</h3>
          </div>
          <div className="neo-grid neo-grid-3">
            {[
              {
                number: '1',
                title: 'Bring Your Problem',
                description: 'A concept. A homework question. A "why does this even exist" rant. All valid starting points.',
                rotation: -2
              },
              {
                number: '2',
                title: 'Learn Your Way',
                description: 'Visual learner? We\'ll draw it out. Need real-world examples? Got those. Want the formal proof? Sure, weirdo, we have that too.',
                rotation: 0
              },
              {
                number: '3',
                title: 'Move On When You\'re Ready',
                description: 'Not when the video ends. Not when the bell rings. When you actually get it.',
                rotation: 2
              }
            ].map((step, idx) => (
              <div
                key={idx}
                className="neo-card neo-card-step neo-card-hover"
                style={{ transform: `rotate(${step.rotation}deg)` }}
              >
                <div className="neo-step-number">{step.number}</div>
                <h4 className="neo-card-title">{step.title}</h4>
                <p className="neo-text-body">{step.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Currently Teaching Section */}
        <section className="neo-section neo-section-white">
          <div className="neo-section-header">
            <h2 className="neo-heading-large">Currently Teaching</h2>
            <h3 className="neo-heading-medium">Math. All of It.</h3>
          </div>
          <div className="neo-card neo-card-lifted" style={{ maxWidth: '800px', margin: '0 auto 40px' }}>
            <ul className="neo-list">
              {[
                'Arithmetic (no shame)',
                'Algebra',
                'Geometry',
                'Trigonometry',
                'Calculus',
                'Statistics',
                'Whatever hybrid monster your curriculum invented'
              ].map((subject, idx) => (
                <li key={idx} className="neo-list-item">
                  <span className="neo-list-bullet" />
                  {subject}
                </li>
              ))}
            </ul>
          </div>
          <div className="neo-card neo-card-yellow neo-card-lifted" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h4 className="neo-card-title">Chemistry & Biology — Coming Soon</h4>
            <p className="neo-text-body">
              We're building those out now. Want early access?{' '}
              <a 
                href="#" 
                onClick={(e) => {
                  e.preventDefault();
                  onGetStarted();
                }}
                className="neo-link"
              >
                Get on the list.
              </a>
            </p>
          </div>
        </section>

        {/* The Honest Truth Section - Black background */}
        <section className="neo-section neo-section-black">
          <div className="neo-section-header">
            <h2 className="neo-heading-large neo-heading-white">The Honest Truth</h2>
            <h3 className="neo-heading-medium neo-heading-white">This Works If You Work</h3>
          </div>
          <div className="neo-card neo-card-white neo-card-lifted" style={{ maxWidth: '900px', margin: '0 auto' }}>
            <p className="neo-text-body">We're not selling magic. We're selling a better tool.</p>
            <p className="neo-text-body">You still have to show up. You still have to try. You still have to do the practice problems.</p>
            <p className="neo-text-body">But when you do? You'll actually understand them. Not just survive them.</p>
            <p className="neo-text-emphasis">The difference between "I passed" and "I get it" is better teaching.</p>
            <p className="neo-text-body">That's what we're here for.</p>
          </div>
        </section>

        {/* Who Gets the Most Out of This Section */}
        <section className="neo-section neo-section-cream">
          <div className="neo-section-header">
            <h2 className="neo-heading-large">Who Gets the Most Out of This</h2>
            <h3 className="neo-heading-medium">Be Honest. Is This You?</h3>
          </div>
          <div className="neo-card neo-card-lifted" style={{ maxWidth: '900px', margin: '0 auto 32px' }}>
            <ul className="neo-list neo-list-check">
              {[
                'You\'ve told yourself you\'re "just not a math person"',
                'You\'ve watched the same concept explained 10 different ways and still don\'t get it',
                'You\'re tired of feeling behind',
                'You learn differently and regular classes don\'t work for you',
                'You want to actually understand, not just pass'
              ].map((item, idx) => (
                <li key={idx} className="neo-list-item neo-list-item-check">
                  <span className="neo-checkbox" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <p className="neo-statement-large">
            If you nodded at any of those, we built this for you.
          </p>
        </section>

        {/* What We're Not Section */}
        <section className="neo-section neo-section-white">
          <div className="neo-section-header">
            <h2 className="neo-heading-large">What We're Not</h2>
            <h3 className="neo-heading-medium">Clarity Is Kindness</h3>
          </div>
          <div className="neo-grid neo-grid-3">
            {[
              {
                title: "We're not a homework cheat code.",
                description: "If you want answers without understanding, go somewhere else. We're not interested.",
                rotation: -1
              },
              {
                title: "We're not replacing your teachers.",
                description: "Good teachers are irreplaceable. We're the support system for when they're not available.",
                rotation: 1
              },
              {
                title: "We're not a miracle.",
                description: "We're a tool. A really good one. But you still have to use it.",
                rotation: -1
              }
            ].map((item, idx) => (
              <div
                key={idx}
                className="neo-card neo-card-cream neo-card-hover"
                style={{ transform: `rotate(${item.rotation}deg)` }}
              >
                <h4 className="neo-card-title">{item.title}</h4>
                <p className="neo-text-body">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* The Pitch Section - CTA */}
        <section className="landing-cta neo-section-cta">
          <div className="neo-badge neo-badge-cta-large" style={{ transform: 'rotate(-3deg)' }}>
            ONE SENTENCE
          </div>
          <h2 className="neo-heading-large">The Pitch</h2>
          <h3 className="neo-heading-medium">One Sentence. No Tricks.</h3>
          <p className="neo-text-large" style={{ maxWidth: '800px', margin: '0 auto 24px' }}>
            A personalized math tutor that's available 24/7, adapts to how you learn, and actually helps you understand.
          </p>
          <p className="neo-text-body" style={{ marginBottom: '40px' }}>
            That's it. That's the product.
          </p>
          <button 
            onClick={onGetStarted}
            className="cta-button cta-button-neo cta-button-large neo-button-press neo-button-pulse"
          >
            Start Learning Now
          </button>
        </section>

        {/* Footer */}
        <footer className="landing-footer neo-footer">
          <h3 className="neo-footer-title">teachr.live</h3>
          <p className="neo-footer-tagline">Finally, teaching that teaches.</p>
          <p className="neo-footer-contact">
            Questions?{' '}
            <a 
              href="mailto:contact@teachr.live" 
              className="neo-link"
            >
              contact@teachr.live
            </a>
          </p>
          <p className="neo-footer-quote">
            Because understanding beats memorizing. Every time.
          </p>
        </footer>
      </div>
    </div>
  );
};

export default LandingPageNeo;

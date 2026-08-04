import React, { useRef } from 'react';
import { NavLink } from 'react-router-dom';
import gsap from 'gsap';
import './SideNavRail.css';

const SideNavRail: React.FC = () => {
  const navRef = useRef<HTMLElement>(null);

  const handleMouseEnter = () => {
    if (navRef.current) {
      gsap.to(navRef.current, { width: 256, duration: 0.3, ease: 'power2.out' });
      gsap.to('.nav-label', { opacity: 1, duration: 0.2, delay: 0.1 });
    }
  };

  const handleMouseLeave = () => {
    if (navRef.current) {
      gsap.to(navRef.current, { width: 64, duration: 0.3, ease: 'power2.inOut' });
      gsap.to('.nav-label', { opacity: 0, duration: 0.1 });
    }
  };

  return (
    <aside 
      ref={navRef}
      className="side-nav-rail"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="nav-top">
        <div className="nav-brand">
          <span className="material-symbols-outlined logo-icon">gavel</span>
          <span className="font-headline-md nav-label brand-name">Trợ lý Pháp lý</span>
        </div>

        <nav className="nav-links">
          <NavLink to="/" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`} end>
            <span className="material-symbols-outlined icon">add</span>
            <span className="font-label-md nav-label">New Chat</span>
          </NavLink>
        </nav>
      </div>

      <div className="nav-bottom">
        <NavLink to="/settings" className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="material-symbols-outlined icon">settings</span>
          <span className="font-label-md nav-label">Settings</span>
        </NavLink>
      </div>
    </aside>
  );
};

export default SideNavRail;

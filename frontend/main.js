// ============================================
// GSTchain Frontend - Main Application
// ============================================

// API Configuration
const API_BASE = '/api';

// ============================================
// Router
// ============================================
class Router {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    window.addEventListener('popstate', () => this.navigate(location.hash.slice(1) || '/'));
  }

  addRoute(path, handler) {
    this.routes[path] = handler;
  }

  navigate(path) {
    if (path !== location.hash.slice(1)) {
      history.pushState(null, '', '#' + path);
    }
    this.currentRoute = path;
    const handler = this.routes[path] || this.routes['/404'];
    if (handler) {
      const app = document.getElementById('app');
      app.innerHTML = '';
      app.className = 'page-enter';
      handler(app);
    }
  }

  start() {
    this.navigate(location.hash.slice(1) || '/');
  }
}

const router = new Router();

// ============================================
// API Service
// ============================================
const api = {
  async uploadInvoice(formData) {
    try {
      // First, we need to parse the PDF - for now, we'll send raw JSON
      const response = await fetch(`${API_BASE}/invoices`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  },

  async verifyInvoice(hash) {
    try {
      const response = await fetch(`${API_BASE}/verify/${hash}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Verification failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Verify error:', error);
      throw error;
    }
  },

  async detectCycles() {
    try {
      const response = await fetch(`${API_BASE}/fraud/detect-cycles`);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Fraud detection failed');
      }
      return await response.json();
    } catch (error) {
      console.error('Fraud detection error:', error);
      throw error;
    }
  },

  async analyzeGSTIN(gstin) {
    try {
      const response = await fetch(`${API_BASE}/fraud/analyze-gstin/${gstin}`);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'GSTIN analysis failed');
      }
      return await response.json();
    } catch (error) {
      console.error('GSTIN analysis error:', error);
      throw error;
    }
  },

  async getRiskRules() {
    try {
      const response = await fetch(`${API_BASE}/fraud/risk-rules`);
      return await response.json();
    } catch (error) {
      console.error('Get rules error:', error);
      throw error;
    }
  },

  async getInvoiceData(hash) {
    try {
      const response = await fetch(`${API_BASE}/invoice/${hash}`);
      return await response.json();
    } catch (error) {
      console.error('Get invoice error:', error);
      throw error;
    }
  },

  async searchByGSTIN(gstin) {
    try {
      // Use the Neo4j-based fraud detection endpoint
      const response = await fetch(`${API_BASE}/fraud/analyze-gstin/${gstin}`);
      return await response.json();
    } catch (error) {
      console.error('GSTIN search error:', error);
      throw error;
    }
  },

  // Authentication API methods
  async registerBusiness(userData) {
    try {
      const response = await fetch(`${API_BASE}/auth/register/business`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }
      return await response.json();
    } catch (error) {
      console.error('Register business error:', error);
      throw error;
    }
  },

  async registerAuditor(userData) {
    try {
      const response = await fetch(`${API_BASE}/auth/register/auditor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }
      return await response.json();
    } catch (error) {
      console.error('Register auditor error:', error);
      throw error;
    }
  },

  async loginBusiness(credentials) {
    try {
      const response = await fetch(`${API_BASE}/auth/login/business`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }
      return await response.json();
    } catch (error) {
      console.error('Login business error:', error);
      throw error;
    }
  },

  async loginAuditor(credentials) {
    try {
      const response = await fetch(`${API_BASE}/auth/login/auditor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }
      return await response.json();
    } catch (error) {
      console.error('Login auditor error:', error);
      throw error;
    }
  },

  async getCurrentUser() {
    try {
      const token = state.authToken;
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error('Invalid session');
      }
      return await response.json();
    } catch (error) {
      console.error('Get user error:', error);
      throw error;
    }
  }
};

// ============================================
// Toast Notifications
// ============================================
const toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 4000) {
    this.init();

    const icons = {
      success: '✓',
      error: '✗',
      warning: '!',
      info: 'i'
    };

    const toastEl = document.createElement('div');
    toastEl.className = `toast toast--${type}`;
    toastEl.innerHTML = `
      <span class="toast__icon">${icons[type]}</span>
      <span class="toast__message">${message}</span>
      <button class="toast__close">×</button>
    `;

    toastEl.querySelector('.toast__close').onclick = () => toastEl.remove();
    this.container.appendChild(toastEl);

    setTimeout(() => toastEl.remove(), duration);
  },

  success(message) { this.show(message, 'success'); },
  error(message) { this.show(message, 'error'); },
  warning(message) { this.show(message, 'warning'); },
  info(message) { this.show(message, 'info'); }
};

// ============================================
// State Management
// ============================================
const state = {
  // Account State
  accounts: [], // Array of { token, user, role }
  activeAccountIndex: -1,

  // Other State
  lastProof: null,
  recentVerifications: [],

  // Getters for backward compatibility
  get authToken() {
    if (this.activeAccountIndex === -1 || !this.accounts[this.activeAccountIndex]) return null;
    return this.accounts[this.activeAccountIndex].token;
  },

  get currentUser() {
    if (this.activeAccountIndex === -1 || !this.accounts[this.activeAccountIndex]) return null;
    return this.accounts[this.activeAccountIndex].user;
  },

  get userRole() {
    if (this.activeAccountIndex === -1 || !this.accounts[this.activeAccountIndex]) return null;
    return this.accounts[this.activeAccountIndex].role;
  },

  init() {
    this.loadFromStorage();
  },

  loadFromStorage() {
    try {
      // Load accounts
      const storedAccounts = localStorage.getItem('accounts');
      const storedActiveIndex = localStorage.getItem('activeAccountIndex');

      if (storedAccounts) {
        this.accounts = JSON.parse(storedAccounts);
        this.activeAccountIndex = storedActiveIndex ? parseInt(storedActiveIndex) : (this.accounts.length > 0 ? 0 : -1);
      } else {
        // Migration from legacy storage if exists
        const legacyToken = localStorage.getItem('authToken');
        const legacyUser = localStorage.getItem('currentUser');
        const legacyRole = localStorage.getItem('userRole');

        if (legacyToken && legacyUser && legacyRole) {
          this.accounts = [{
            token: legacyToken,
            user: JSON.parse(legacyUser),
            role: legacyRole
          }];
          this.activeAccountIndex = 0;
          this.saveAuth();
        }
      }

      const lastProof = localStorage.getItem('lastProof');
      if (lastProof) this.lastProof = JSON.parse(lastProof);

      const verifications = localStorage.getItem('recentVerifications');
      if (verifications) this.recentVerifications = JSON.parse(verifications);
    } catch (e) {
      console.error('Error loading state:', e);
      this.accounts = [];
      this.activeAccountIndex = -1;
    }
  },

  saveAuth() {
    localStorage.setItem('accounts', JSON.stringify(this.accounts));
    localStorage.setItem('activeAccountIndex', this.activeAccountIndex);
  },

  saveProof(proof) {
    this.lastProof = proof;
    localStorage.setItem('lastProof', JSON.stringify(proof));
  },

  addVerification(verification) {
    this.recentVerifications.unshift(verification);
    this.recentVerifications = this.recentVerifications.slice(0, 10);
    localStorage.setItem('recentVerifications', JSON.stringify(this.recentVerifications));
  },

  login(token, user, role) {
    // Check if account already exists
    const existingIndex = this.accounts.findIndex(acc => acc.user.email === user.email);

    if (existingIndex !== -1) {
      this.accounts[existingIndex] = { token, user, role };
      this.activeAccountIndex = existingIndex;
    } else {
      // Enforce role consistency
      if (this.accounts.length > 0) {
        const currentRole = this.accounts[0].role;
        if (role !== currentRole) {
          alert(`You are currently logged in as a ${currentRole}. Please logout to switch roles.`);
          return false;
        }
      }
      this.accounts.push({ token, user, role });
      this.activeAccountIndex = this.accounts.length - 1;
    }

    this.saveAuth();
    return true;
  },

  logout() {
    if (this.activeAccountIndex !== -1) {
      this.accounts.splice(this.activeAccountIndex, 1);

      if (this.accounts.length > 0) {
        this.activeAccountIndex = 0;
        this.saveAuth();
        window.location.reload();
        return;
      }
    }

    this.activeAccountIndex = -1;
    this.accounts = [];
    localStorage.removeItem('accounts');
    localStorage.removeItem('activeAccountIndex');

    // Clear legacy
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('userRole');
  },

  switchAccount(index) {
    if (index >= 0 && index < this.accounts.length) {
      this.activeAccountIndex = index;
      this.saveAuth();
      window.location.reload();
    }
  },

  isAuthenticated() {
    return this.accounts.length > 0 && this.activeAccountIndex !== -1;
  }
};

// ============================================
// Header Component
// ============================================
function renderHeader(showNav = true, hideDashboardLink = false) {
  const isLoggedIn = state.isAuthenticated();
  const userName = state.currentUser?.name || '';

  return `
    <header class="header">
      <a href="#/" class="header__logo">
        <span>GSTchain</span>
      </a>
      ${showNav ? `
        <nav class="header__nav">
          ${isLoggedIn ? `
            ${!hideDashboardLink ? `
            <a href="#/${state.userRole === 'business' ? 'business' : 'regulator'}" class="header__nav-link header__nav-link--active">
              Dashboard
            </a>
            ` : ''}
            <div class="user-dropdown" style="position: relative; margin-left: 16px;">
              <button class="btn btn--small user-dropdown__trigger" onclick="toggleUserDropdown(event)" style="display: flex; align-items: center; gap: 8px;">
                <span>${userName}</span>
                <span style="font-size: 10px;">▼</span>
              </button>
              <div id="user-dropdown-menu" class="user-dropdown__menu hidden" style="position: absolute; top: 100%; right: 0; margin-top: 8px; background: white; border: 3px solid black; box-shadow: 8px 8px 0 rgba(0,0,0,0.2); min-width: 250px; z-index: 100;">
                
                ${state.accounts.map((acc, index) => {
    const isCurrent = index === state.activeAccountIndex;
    const accName = acc.user.name || acc.user.full_name || acc.user.email;
    return `
                    <div 
                      onclick="${!isCurrent ? `switchAccount(${index})` : ''}"
                      style="padding: 12px 16px; border-bottom: 1px solid #eee; cursor: ${isCurrent ? 'default' : 'pointer'}; background: ${isCurrent ? '#f9f9f9' : 'white'}; display: flex; align-items: center; justify-content: space-between;"
                      onmouseover="this.style.background='${isCurrent ? '#f9f9f9' : '#f5f5f5'}'" 
                      onmouseout="this.style.background='${isCurrent ? '#f9f9f9' : 'white'}'"
                    >
                      <div>
                        <div style="font-weight: 600; font-size: 0.9rem; color: #333;">${accName}</div>
                        <div style="font-size: 0.75rem; color: #666;">${acc.user.email}</div>
                      </div>
                      ${isCurrent ? '<span style="color: green; font-weight: bold; font-size: 0.8rem;">Active</span>' : ''}
                    </div>
                  `;
  }).join('')}

                <button onclick="router.navigate('/login/${state.userRole}')" style="width: 100%; padding: 12px 16px; background: none; border: none; text-align: left; cursor: pointer; font-size: 0.85rem; color: #0066cc; border-bottom: 1px solid #eee;" onmouseover="this.style.background='#f5f5f5'" onmouseout="this.style.background='none'">
                  + Add another account
                </button>

                <button onclick="handleLogout()" style="width: 100%; padding: 12px 16px; background: none; border: none; text-align: left; cursor: pointer; font-size: 0.95rem; font-weight: 500; color: #d32f2f;" onmouseover="this.style.background='#fff0f0'" onmouseout="this.style.background='none'">
                  Logout
                </button>
              </div>
            </div>
          ` : `
            <a href="#/select-role" class="header__nav-link">Login</a>
          `}
        </nav>
      ` : ''}
    </header>
  `;
}

// ============================================
// Footer Component
// ============================================
function renderFooter() {
  return `
    <footer class="footer">
      <div class="footer__content">
        <div>
          <div class="footer__logo">GSTchain</div>
          <p class="footer__text">
            Blockchain-powered GST invoice verification and fraud detection system. 
            Ensuring tamper-proof compliance for the digital age.
          </p>
        </div>
        <div>
          <h4 class="footer__title">Technology</h4>
          <a href="#" class="footer__link">Ethereum Blockchain</a>
          <a href="#" class="footer__link">AES-256 Encryption</a>
          <a href="#" class="footer__link">SHA-256 Hashing</a>
          <a href="#" class="footer__link">Neo4j Graph DB</a>
        </div>
        <div>
          <h4 class="footer__title">Resources</h4>
          <a href="#/about" class="footer__link">About</a>
          <a href="#" class="footer__link">Documentation</a>
          <a href="#" class="footer__link">API Reference</a>
          <a href="#" class="footer__link">Support</a>
        </div>
      </div>
      <div class="footer__bottom">
        <p>© 2026 GSTCHAIN by Saad & Shloka. Built for secure tax compliance.</p>
      </div>
    </footer>
  `;
}

// ============================================
// Animation Utilities
// ============================================
function initScrollAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target); // Only animate once
      }
    });
  }, observerOptions);

  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    observer.observe(el);
  });
}

// ============================================
// Landing Page
// ============================================
function renderLanding(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main>
      <!-- Hero Section -->
      <section class="hero hero--centered">
        <div class="container">
          <div class="hero__content hero__content--large">
            <div class="hero__badge animate-on-scroll animate-fade-up">Blockchain Secured</div>
            <h1 class="hero__title hero__title--large animate-on-scroll animate-fade-up delay-100">
              Tamper-Proof<br>
              <span>GST Invoices</span>
            </h1>
            <p class="hero__subtitle hero__subtitle--large animate-on-scroll animate-fade-up delay-200">
              The future of tax compliance is here. Upload invoices, get cryptographic proof, 
              and verify authenticity instantly with blockchain-anchored evidence.
            </p>
            <div class="hero__cta animate-on-scroll animate-fade-up delay-300">
              <button class="btn btn--primary btn--large" onclick="router.navigate('/select-role')">
                Get Started
              </button>
              <button class="btn btn--large" onclick="router.navigate('/about')">
                Learn More
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Features Section -->
      <section class="features section">
        <div class="container">
          <h2 class="text-center mb-2xl animate-on-scroll animate-fade-up">Why GSTchain?</h2>
          <div class="bento-grid">
            
            <!-- Key Feature 1 (Large) -->
            <div class="feature-card feature-card--large col-span-2 animate-on-scroll animate-fade-up delay-100">
              <div>
                <h3 class="feature-card__title">Blockchain Anchored</h3>
                <p>Every invoice hash is anchored to Ethereum, creating an immutable timestamp that can never be altered or deleted. Verification is decentralized and trustless.</p>
              </div>
            </div>

            <!-- Key Feature 2 (Large) -->
            <div class="feature-card feature-card--large col-span-2 animate-on-scroll animate-fade-up delay-200">
              <div>
                <h3 class="feature-card__title">Instant Verification</h3>
                <p>Regulators and tax officers can verify the authenticity of any invoice in milliseconds using our cryptographic proof engine. No manual audits required.</p>
              </div>
            </div>

            <!-- Standard Features Row -->
            <div class="feature-card col-span-1 animate-on-scroll animate-fade-up delay-300">
              <h3 class="feature-card__title">Military-Grade Encryption</h3>
              <p>AES-256-GCM encryption ensures your sensitive invoice data remains private and accessible only to you.</p>
            </div>
            
            <div class="feature-card col-span-1 animate-on-scroll animate-fade-up delay-400">
              <h3 class="feature-card__title">Fraud Detection</h3>
              <p>Our graph AI automatically detects circular trading loops and suspicious supplier networks.</p>
            </div>

            <div class="feature-card col-span-1 animate-on-scroll animate-fade-up delay-500">
              <h3 class="feature-card__title">Audit Trail</h3>
              <p>Get a complete, tamper-proof history of every document's lifecycle from creation to filing.</p>
            </div>

            <div class="feature-card col-span-1 animate-on-scroll animate-fade-up delay-600">
              <h3 class="feature-card__title">Cloud Native</h3>
              <p>Built on highly durable cloud storage with global availability and redundant backups.</p>
            </div>
            
          </div>
        </div>
      </section>

      <!-- How It Works Section -->
      <section class="section">
        <div class="container">
          <h2 class="text-center mb-2xl animate-on-scroll animate-fade-up">How It Works</h2>
          
          <div class="timeline">
            <!-- Step 1 -->
            <div class="timeline-step animate-on-scroll animate-fade-right delay-100">
              <div class="timeline-dot">1</div>
              <div class="timeline-content">
                <h4>Upload Invoice</h4>
                <p>Upload your GST invoice PDF. Our system extracts and validates all data automatically using OCR and schema checks.</p>
              </div>
            </div>

            <!-- Step 2 -->
            <div class="timeline-step animate-on-scroll animate-fade-right delay-200">
              <div class="timeline-dot">2</div>
              <div class="timeline-content">
                <h4>Generate Hash</h4>
                <p>A unique SHA-256 fingerprint is created from the canonicalized invoice data. This ensures that even a single byte change will invalidate the hash.</p>
              </div>
            </div>

            <!-- Step 3 -->
            <div class="timeline-step animate-on-scroll animate-fade-right delay-300">
              <div class="timeline-dot">3</div>
              <div class="timeline-content">
                <h4>Encrypt & Store</h4>
                <p>Data is encrypted with AES-256-GCM and stored securely in decentralized cloud storage, ensuring privacy and availability.</p>
              </div>
            </div>

            <!-- Step 4 -->
            <div class="timeline-step animate-on-scroll animate-fade-right delay-400">
              <div class="timeline-dot">4</div>
              <div class="timeline-content">
                <h4>Anchor to Blockchain</h4>
                <p>The hash is permanently recorded on the Ethereum blockchain with a verifiable transaction ID, proving the document existed at that specific time.</p>
              </div>
            </div>
          </div>

        </div>
      </section>

      <!-- CTA Section -->
      <section class="section section--alt">
        <div class="container text-center">
          <h2 class="mb-lg animate-on-scroll animate-fade-up">Ready to Secure Your Invoices?</h2>
          <p class="mb-2xl animate-on-scroll animate-fade-up delay-100" style="max-width: 600px; margin-left: auto; margin-right: auto;">
            Join the future of tax compliance. Whether you're a business seeking proof or a regulator verifying authenticity.
          </p>
          <button class="btn btn--primary btn--large animate-on-scroll animate-pop delay-200" onclick="router.navigate('/select-role')">
            Choose Your Role
          </button>
        </div>
      </section>
    </main>

    ${renderFooter()}
  `;

  // Initialize animations after rendering
  setTimeout(initScrollAnimations, 50);
}

// ============================================
// Role Selection Page
// ============================================
function renderRoleSelection(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main class="role-selection">
      <div class="container">
        <h2 class="text-center mb-lg">Choose Your Role</h2>
        <p class="text-center mb-2xl" style="color: #666; max-width: 500px; margin-left: auto; margin-right: auto;">
          Select your role to access the appropriate portal and features.
        </p>
        
        <div class="role-selection__cards">
          <div class="card card--accent-yellow role-card" onclick="router.navigate('/login/business')">
            <h3 class="role-card__title">Business User</h3>
            <p class="role-card__desc">
              Upload invoices and get cryptographic proof. Perfect for businesses who need tamper-proof evidence.
            </p>
          </div>
          
          <div class="card card--primary role-card" onclick="router.navigate('/login/auditor')">
            <h3 class="role-card__title">Auditor</h3>
            <p class="role-card__desc">
              Verify invoice authenticity and detect tampering. Built for auditors and compliance officers.
            </p>
          </div>
        </div>
      </div>
    </main>

    ${renderFooter()}
  `;
}

function selectRole(role) {
  state.setRole(role);
  toast.success(`Welcome! You're now in ${role === 'business' ? 'Business' : 'Regulator'} mode.`);
  router.navigate(role === 'business' ? '/business' : '/regulator');
}

// ============================================
// Business Dashboard
// ============================================
function renderBusinessDashboard(container) {
  // Auth guard - redirect to login if not authenticated
  if (!state.isAuthenticated()) {
    toast.warning('Please login to access the dashboard');
    router.navigate('/login/business');
    return;
  }

  const lastProof = state.lastProof;

  container.innerHTML = `
    ${renderHeader(true, true)}
    
    <div class="dashboard">
      <aside class="dashboard__sidebar">
        <nav class="dashboard__nav">
          <div class="dashboard__nav-item dashboard__nav-item--active" onclick="router.navigate('/business')">
            Dashboard
          </div>
          <div class="dashboard__nav-item" onclick="router.navigate('/upload')">
            Upload Invoice
          </div>
          ${lastProof ? `
            <div class="dashboard__nav-item" onclick="router.navigate('/proof')">
              View Last Proof
            </div>
          ` : ''}
        </nav>
      </aside>
      
      <main class="dashboard__main">
        <div class="dashboard__header">
          <h1 class="dashboard__title">Business Dashboard</h1>
          <p class="dashboard__subtitle">Upload invoices and manage your cryptographic proofs</p>
        </div>
        
        <div class="stats-grid">
          <div class="card stat-card card--accent-yellow">
            <div class="stat-card__value">${lastProof ? '1' : '0'}</div>
            <div class="stat-card__label">Invoices Uploaded</div>
          </div>
          <div class="card stat-card card--accent-green">
            <div class="stat-card__value">${lastProof ? '1' : '0'}</div>
            <div class="stat-card__label">Blockchain Anchored</div>
          </div>
          <div class="card stat-card card--accent-cyan">
            <div class="stat-card__value">${lastProof ? '✓' : '—'}</div>
            <div class="stat-card__label">Last Upload Status</div>
          </div>
        </div>
        
        <div class="card">
          <h3 class="mb-lg">Quick Actions</h3>
          <div class="flex flex--gap-lg" style="flex-wrap: wrap;">
            <button class="btn btn--primary" onclick="router.navigate('/upload')">
              Upload New Invoice
            </button>
            ${lastProof ? `
              <button class="btn" onclick="router.navigate('/proof')">
                View Last Proof
              </button>
            ` : ''}
          </div>
        </div>
        
        ${lastProof ? `
          <div class="card mt-xl">
            <h3 class="mb-lg">Recent Upload</h3>
            <div class="proof__item">
              <div class="proof__item-label">Invoice Hash</div>
              <div class="hash-display">
                <span>${lastProof.invoice_hash}</span>
                <button class="hash-display__copy" onclick="copyToClipboard('${lastProof.invoice_hash}')">Copy</button>
              </div>
            </div>
          </div>
        ` : ''}
      </main>
    </div>
  `;
}

// ============================================
// Upload Page
// ============================================
function renderUploadPage(container) {
  // Auth guard - redirect to login if not authenticated
  if (!state.isAuthenticated()) {
    toast.warning('Please login to access this page');
    router.navigate('/login/business');
    return;
  }

  const lastProof = state.lastProof;

  container.innerHTML = `
    ${renderHeader()}
    
    <div class="dashboard">
      <aside class="dashboard__sidebar">
        <nav class="dashboard__nav">
          <div class="dashboard__nav-item" onclick="router.navigate('/business')">
            Dashboard
          </div>
          <div class="dashboard__nav-item dashboard__nav-item--active">
            Upload Invoice
          </div>
          ${lastProof ? `
            <div class="dashboard__nav-item" onclick="router.navigate('/proof')">
              View Last Proof
            </div>
          ` : ''}
        </nav>
      </aside>
      
      <main class="dashboard__main">
        <div class="dashboard__header">
          <h1 class="dashboard__title">Upload Invoice</h1>
          <p class="dashboard__subtitle">Upload your GST invoice to get a blockchain-anchored proof</p>
        </div>
        
        <div class="card card--no-hover">
          <div id="upload-zone" class="upload-zone" ondrop="handleDrop(event)" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)">
            <div class="upload-zone__text">Drop your invoice PDF here</div>
            <div class="upload-zone__subtext">or click to browse files</div>
            <input type="file" id="file-input" accept=".pdf,.json" style="display: none;" onchange="handleFileSelect(event)">
          </div>
          
          <div id="upload-preview" class="hidden mt-xl">
            <div class="flex flex--between" style="align-items: center;">
              <div>
                <strong id="file-name"></strong>
                <span id="file-size" style="color: #666; margin-left: 8px;"></span>
              </div>
              <button class="btn btn--small" onclick="clearFile()">Remove</button>
            </div>
          </div>
          
          <div id="upload-progress" class="hidden mt-xl">
            <div class="progress">
              <div class="progress__bar" id="progress-bar" style="width: 0%"></div>
            </div>
            <p class="mt-md text-center" id="progress-text">Processing...</p>
          </div>
        </div>
        
        <div class="card mt-xl card--no-hover">
          <h3 class="mb-lg">Or Enter Invoice Data Manually</h3>
          <p class="mb-lg" style="color: #666;">For demo purposes, you can submit sample invoice data directly.</p>
          
          <form id="manual-form" onsubmit="handleManualSubmit(event)">
            <div class="grid grid--2" style="gap: 16px;">
              <div class="input-group">
                <label class="input-label">Invoice ID</label>
                <input type="text" class="input" name="invoice_id" value="INV-2026-001" required>
              </div>
              <div class="input-group">
                <label class="input-label">Invoice Date</label>
                <input type="date" class="input" name="invoice_date" value="2026-01-21" required>
              </div>
              <div class="input-group">
                <label class="input-label">Supplier GSTIN</label>
                <input type="text" class="input" name="supplier_gstin" value="27ABCDE1234F2Z5" required>
              </div>
              <div class="input-group">
                <label class="input-label">Recipient GSTIN</label>
                <input type="text" class="input" name="recipient_gstin" value="27ZZZZZ1234Z1Z9" required>
              </div>
              <div class="input-group">
                <label class="input-label">Grand Total (₹)</label>
                <input type="number" class="input" name="grand_total" value="11800" step="0.01" required>
              </div>
              <div class="input-group">
                <label class="input-label">Supply Type</label>
                <select class="input" name="supply_type">
                  <option value="B2B">B2B</option>
                  <option value="B2C">B2C</option>
                  <option value="E-INV">E-Invoice</option>
                </select>
              </div>
            </div>
            
            <button type="submit" class="btn btn--primary btn--large mt-xl" style="width: 100%;">
              Anchor to Blockchain
            </button>
          </form>
        </div>
      </main>
    </div>
  `;

  // Setup file input click handler
  document.getElementById('upload-zone').onclick = () => {
    document.getElementById('file-input').click();
  };
}

let selectedFile = null;

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.add('upload-zone--active');
}

function handleDragLeave(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.remove('upload-zone--active');
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('upload-zone').classList.remove('upload-zone--active');

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
}

function handleFile(file) {
  selectedFile = file;
  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-size').textContent = `(${(file.size / 1024).toFixed(1)} KB)`;
  document.getElementById('upload-preview').classList.remove('hidden');

  toast.info(`File "${file.name}" selected. Ready to process!`);
}

function clearFile() {
  selectedFile = null;
  document.getElementById('upload-preview').classList.add('hidden');
  document.getElementById('file-input').value = '';
}

async function handleManualSubmit(e) {
  e.preventDefault();

  const form = e.target;
  const formData = {
    header: {
      invoice_id: form.invoice_id.value,
      invoice_date: form.invoice_date.value,
      currency: 'INR'
    },
    supplier: {
      gstin: form.supplier_gstin.value,
      name: 'Demo Supplier Pvt Ltd'
    },
    recipient: {
      gstin: form.recipient_gstin.value,
      name: 'Demo Recipient Co'
    },
    totals: {
      grand_total: parseFloat(form.grand_total.value),
      total_taxable_value: parseFloat(form.grand_total.value) * 0.82,
      cgst_total: parseFloat(form.grand_total.value) * 0.09,
      sgst_total: parseFloat(form.grand_total.value) * 0.09
    },
    invoice_metadata: {
      supply_type: form.supply_type.value,
      is_einvoice: form.supply_type.value === 'E-INV'
    },
    items: []
  };

  // Show progress
  document.getElementById('upload-progress').classList.remove('hidden');
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');

  // Simulate progress stages
  const stages = [
    { width: 20, text: 'Canonicalizing invoice data...' },
    { width: 40, text: 'Generating SHA-256 hash...' },
    { width: 60, text: 'Encrypting with AES-256-GCM...' },
    { width: 80, text: 'Anchoring to Polygon Amoy blockchain...' },
    { width: 100, text: 'Complete!' }
  ];

  try {
    for (let i = 0; i < stages.length - 1; i++) {
      progressBar.style.width = stages[i].width + '%';
      progressText.textContent = stages[i].text;
      await new Promise(r => setTimeout(r, 500));
    }

    const result = await api.uploadInvoice(formData);

    progressBar.style.width = '100%';
    progressText.textContent = 'Complete!';

    state.saveProof(result);
    toast.success('Invoice anchored to blockchain successfully!');

    setTimeout(() => {
      router.navigate('/proof');
    }, 1000);

  } catch (error) {
    document.getElementById('upload-progress').classList.add('hidden');
    toast.error(`Upload failed: ${error.message}`);
  }
}

// ============================================
// Proof Display Page
// ============================================
function renderProofPage(container) {
  // Auth guard - redirect to login if not authenticated
  if (!state.isAuthenticated()) {
    toast.warning('Please login to access this page');
    router.navigate('/login/business');
    return;
  }

  const proof = state.lastProof;

  if (!proof) {
    container.innerHTML = `
      ${renderHeader()}
      <div class="container section text-center">
        <h2>No Proof Available</h2>
        <p class="mt-lg mb-xl">You haven't uploaded any invoices yet.</p>
        <button class="btn btn--primary" onclick="router.navigate('/upload')">Upload Invoice</button>
      </div>
      ${renderFooter()}
    `;
    return;
  }

  container.innerHTML = `
    ${renderHeader()}
    
    <div class="dashboard">
      <aside class="dashboard__sidebar">
        <nav class="dashboard__nav">
          <div class="dashboard__nav-item" onclick="router.navigate('/business')">
            Dashboard
          </div>
          <div class="dashboard__nav-item" onclick="router.navigate('/upload')">
            Upload Invoice
          </div>
          <div class="dashboard__nav-item dashboard__nav-item--active">
            View Last Proof
          </div>
        </nav>
      </aside>
      
      <main class="dashboard__main">
        <div class="proof">
          <div class="proof__header">
            <div class="proof__success-icon">✓</div>
            <h1>Invoice Anchored Successfully</h1>
            <p style="color: #666;">Your invoice has been encrypted, stored, and anchored to the blockchain.</p>
          </div>
          
          <div class="proof__details">
            <div class="card proof__item">
              <div class="proof__item-label">Invoice Hash (SHA-256)</div>
              <div class="hash-display">
                <span>${proof.invoice_hash}</span>
                <button class="hash-display__copy" onclick="copyToClipboard('${proof.invoice_hash}')">Copy</button>
              </div>
              <p class="mt-md" style="color: #666; font-size: 0.875rem;">
                This is the unique cryptographic fingerprint of your invoice. Share this with anyone who needs to verify the invoice.
              </p>
            </div>
            
            <div class="card proof__item card--accent-cyan">
              <div class="proof__item-label">Blockchain Transaction ID</div>
              <div class="hash-display">
                <span>${proof.onchain_txid}</span>
                <button class="hash-display__copy" onclick="copyToClipboard('${proof.onchain_txid}')">Copy</button>
              </div>
              <p class="mt-md" style="font-size: 0.875rem;">
                <a href="https://amoy.polygonscan.com/tx/${proof.onchain_txid}" target="_blank" style="color: inherit; text-decoration: underline;">
                  View on Polygonscan →
                </a>
              </p>
            </div>
            
            <div class="card proof__item">
              <div class="proof__item-label">Ingestion ID</div>
              <code style="font-size: 0.875rem;">${proof.ingestion_id}</code>
            </div>
            
            <div class="card proof__item">
              <div class="proof__item-label">Storage Path</div>
              <code style="font-size: 0.875rem;">${proof.object_path}</code>
            </div>
          </div>
          
          <div class="flex flex--gap-lg mt-2xl" style="justify-content: center; flex-wrap: wrap;">
            <button class="btn btn--accent" onclick="viewInvoiceJSON('${proof.invoice_hash}')">
              View Invoice JSON
            </button>
            <button class="btn btn--primary" onclick="downloadProof()">
              Download Proof
            </button>
            <button class="btn" onclick="router.navigate('/upload')">
              Upload Another
            </button>
          </div>
          
          <div id="invoice-json-modal" class="hidden mt-xl">
            <div class="card card--no-hover" style="background: #1a1a1a; color: #22C55E;">
              <div class="flex flex--between mb-md">
                <h4 style="color: #fff;">Invoice JSON Data</h4>
                <button class="btn btn--small" onclick="document.getElementById('invoice-json-modal').classList.add('hidden')">✕ Close</button>
              </div>
              <pre id="invoice-json-content" style="overflow-x: auto; font-size: 0.8rem; max-height: 400px; overflow-y: auto;"></pre>
            </div>
          </div>
        </div>
      </main>
    </div>
  `;
}

function downloadProof() {
  const proof = state.lastProof;
  if (!proof) return;

  const content = `
GSTchain - Invoice Proof Certificate
=====================================

Date Generated: ${new Date().toISOString()}

INVOICE HASH (SHA-256):
${proof.invoice_hash}

BLOCKCHAIN TRANSACTION:
${proof.onchain_txid}

INGESTION ID:
${proof.ingestion_id}

STORAGE LOCATION:
${proof.object_path}

VERIFICATION:
To verify this invoice, visit GSTchain and enter the Invoice Hash above.
The system will confirm if the invoice is authentic and untampered.

This proof is cryptographically secured and blockchain-anchored.
  `.trim();

  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `gstchain-proof-${proof.invoice_hash.slice(0, 8)}.txt`;
  a.click();
  URL.revokeObjectURL(url);

  toast.success('Proof certificate downloaded!');
}

// ============================================
// Regulator Dashboard
// ============================================
function renderRegulatorDashboard(container) {
  // Auth guard - redirect to login if not authenticated
  if (!state.isAuthenticated()) {
    toast.warning('Please login to access the dashboard');
    router.navigate('/login/auditor');
    return;
  }

  const recentVerifications = state.recentVerifications;

  container.innerHTML = `
    ${renderHeader(true, true)}
    
    <div class="dashboard">
      <aside class="dashboard__sidebar">
        <nav class="dashboard__nav">
          <div class="dashboard__nav-item dashboard__nav-item--active" onclick="router.navigate('/regulator')">
            Dashboard
          </div>
          <div class="dashboard__nav-item" onclick="router.navigate('/verify')">
            Verify Invoice
          </div>
          <div class="dashboard__nav-item" onclick="router.navigate('/fraud-detection')">
            Cycle Detection
          </div>
        </nav>
      </aside>
      
      <main class="dashboard__main">
        <div class="dashboard__header">
          <h1 class="dashboard__title">Regulator Dashboard</h1>
          <p class="dashboard__subtitle">Verify invoice authenticity and detect tampering</p>
        </div>
        
        <div class="stats-grid">
          <div class="card stat-card card--primary">
            <div class="stat-card__value">${recentVerifications.length}</div>
            <div class="stat-card__label">Verifications Performed</div>
          </div>
          <div class="card stat-card card--accent-green">
            <div class="stat-card__value">${recentVerifications.filter(v => v.valid).length}</div>
            <div class="stat-card__label">Valid Invoices</div>
          </div>
          <div class="card stat-card card--accent-pink">
            <div class="stat-card__value">${recentVerifications.filter(v => v.tampered).length}</div>
            <div class="stat-card__label">Tampered Detected</div>
          </div>
        </div>
        
        <div class="card">
          <h3 class="mb-lg">Quick Verify</h3>
          <form onsubmit="quickVerify(event)" class="verify-form__input-group">
            <input type="text" class="input verify-form__input" id="quick-verify-hash" placeholder="Enter invoice hash..." required>
            <button type="submit" class="btn btn--primary">Verify</button>
          </form>
        </div>
        
        ${recentVerifications.length > 0 ? `
          <div class="card mt-xl">
            <h3 class="mb-lg">Recent Verifications</h3>
            <div class="flex flex--column flex--gap-md">
              ${recentVerifications.map(v => `
                <div class="flex flex--between" style="align-items: center; padding: 12px; background: ${v.valid ? '#ECFDF5' : '#FEF2F2'}; border: 3px solid var(--color-black);">
                  <div>
                    <code style="font-size: 0.8rem;">${v.hash.slice(0, 20)}...</code>
                    <span class="badge badge--${v.valid ? 'success' : 'error'}" style="margin-left: 8px;">
                      ${v.valid ? 'VALID' : v.tampered ? 'TAMPERED' : 'NOT FOUND'}
                    </span>
                  </div>
                  <button class="btn btn--small" onclick="router.navigate('/verify-result/${v.hash}')">View</button>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </main>
    </div>
  `;
}

function quickVerify(e) {
  e.preventDefault();
  const hash = document.getElementById('quick-verify-hash').value.trim();
  if (hash) {
    router.navigate(`/verify/${hash}`);
  }
}

// ============================================
// Verify Page
// ============================================
function renderVerifyPage(container) {
  // Auth guard - redirect to login if not authenticated
  if (!state.isAuthenticated()) {
    toast.warning('Please login to access this page');
    router.navigate('/login/auditor');
    return;
  }

  container.innerHTML = `
    ${renderHeader()}
    
    <div class="dashboard">
      <aside class="dashboard__sidebar">
        <nav class="dashboard__nav">
          <div class="dashboard__nav-item" onclick="router.navigate('/regulator')">
            Dashboard
          </div>
          <div class="dashboard__nav-item dashboard__nav-item--active">
            Verify Invoice
          </div>
          <div class="dashboard__nav-item" onclick="router.navigate('/fraud-detection')">
            Cycle Detection
          </div>
        </nav>
      </aside>
      
      <main class="dashboard__main">
        <div class="dashboard__header">
          <h1 class="dashboard__title">Verify Invoice</h1>
          <p class="dashboard__subtitle">Enter an invoice hash to verify its authenticity and check for tampering.</p>
        </div>
        
        <div class="card card--no-hover" style="max-width: 600px; margin: 0 auto;">
            <form onsubmit="performVerification(event)" id="verify-form">
              <div class="input-group mb-xl">
                <label class="input-label">Invoice Hash</label>
                <input type="text" class="input input--large" id="verify-hash" 
                       placeholder="e.g., a1b2c3d4e5f6..." required
                       style="font-family: monospace;">
              </div>
              
              <button type="submit" class="btn btn--primary btn--large" style="width: 100%;">
                Verify Invoice
              </button>
            </form>
            
            <div id="verify-loading" class="hidden loading mt-xl">
              <div class="loading__spinner"></div>
              <div class="loading__text">Verifying invoice...</div>
            </div>
          </div>
          
          <div class="card mt-xl">
            <h4 class="mb-md">What happens during verification?</h4>
            <ol style="padding-left: 20px; color: #666;">
              <li style="margin-bottom: 8px;">The system retrieves the encrypted invoice from secure storage</li>
              <li style="margin-bottom: 8px;">The invoice is decrypted using the master key</li>
              <li style="margin-bottom: 8px;">A new hash is computed from the decrypted data</li>
              <li style="margin-bottom: 8px;">The computed hash is compared to the original</li>
              <li>Blockchain records are checked for immutability proof</li>
            </ol>
          </div>
        </div>
      </main>
    </div>
  `;
}

async function performVerification(e) {
  e.preventDefault();
  const hash = document.getElementById('verify-hash').value.trim();

  document.getElementById('verify-loading').classList.remove('hidden');
  document.getElementById('verify-form').style.opacity = '0.5';

  try {
    const result = await api.verifyInvoice(hash);

    // Store the verification
    state.addVerification({
      hash,
      ...result,
      timestamp: new Date().toISOString()
    });

    // Navigate to results
    localStorage.setItem('lastVerifyResult', JSON.stringify({ hash, ...result }));
    router.navigate('/verify-result');

  } catch (error) {
    document.getElementById('verify-loading').classList.add('hidden');
    document.getElementById('verify-form').style.opacity = '1';

    // Store failed verification
    state.addVerification({
      hash,
      valid: false,
      reason: error.message,
      timestamp: new Date().toISOString()
    });

    toast.error(`Verification failed: ${error.message}`);
  }
}

// ============================================
// Verify Result Page
// ============================================
function renderVerifyResultPage(container) {
  // Auth guard - redirect to login if not authenticated
  if (!state.isAuthenticated()) {
    toast.warning('Please login to access this page');
    router.navigate('/login/auditor');
    return;
  }

  const result = JSON.parse(localStorage.getItem('lastVerifyResult') || 'null');

  if (!result) {
    router.navigate('/verify');
    return;
  }

  const isValid = result.valid;
  const isTampered = result.tampered;

  container.innerHTML = `
    ${renderHeader()}
    
    <div class="dashboard">
      <aside class="dashboard__sidebar">
        <nav class="dashboard__nav">
          <div class="dashboard__nav-item" onclick="router.navigate('/regulator')">
            Dashboard
          </div>
          <div class="dashboard__nav-item" onclick="router.navigate('/verify')">
            Verify Invoice
          </div>
          <div class="dashboard__nav-item dashboard__nav-item--active">
            Result
          </div>
        </nav>
      </aside>
      
      <main class="dashboard__main">
        <div class="container--narrow" style="margin: 0 auto;">
          <div class="card status-card ${isValid ? 'status-card--valid' : (isTampered ? 'status-card--tampered' : 'status-card--invalid')}">
            <div class="status-card__icon">${isValid ? '✓' : '✗'}</div>
            <h1 class="status-card__title">
              ${isValid ? 'Invoice Verified' : (isTampered ? 'TAMPERING DETECTED!' : 'Verification Failed')}
            </h1>
            <p>
              ${isValid
      ? 'This invoice is authentic and has not been tampered with.'
      : (isTampered
        ? 'WARNING: This invoice has been modified after anchoring!'
        : result.reason || 'Invoice could not be verified.')}
            </p>
          </div>
          
          <div class="proof__details mt-2xl">
            <div class="card proof__item">
              <div class="proof__item-label">Verified Hash</div>
              <div class="hash-display">
                <span>${result.hash}</span>
                <button class="hash-display__copy" onclick="copyToClipboard('${result.hash}')">Copy</button>
              </div>
            </div>
            
            <div class="grid grid--2" style="gap: 16px;">
              <div class="card ${result.hash_match ? 'card--accent-green' : 'card--accent-pink'}">
                <strong>Hash Match</strong>
                <div style="font-size: 2rem; margin-top: 8px;">${result.hash_match ? '✓' : '✗'}</div>
              </div>
              <div class="card ${result.onchain ? 'card--accent-green' : 'card--accent-yellow'}">
                <strong>On Blockchain</strong>
                <div style="font-size: 2rem; margin-top: 8px;">${result.onchain ? '✓' : '—'}</div>
              </div>
            </div>
            
            ${result.onchain_txid ? `
              <div class="card proof__item">
                <div class="proof__item-label">Blockchain Transaction</div>
                <div class="hash-display">
                  <span>${result.onchain_txid}</span>
                  <button class="hash-display__copy" onclick="copyToClipboard('${result.onchain_txid}')">Copy</button>
                </div>
                <p class="mt-md">
                  <a href="https://amoy.polygonscan.com/tx/0x${result.onchain_txid}" target="_blank" style="color: var(--color-primary); text-decoration: underline;">
                    View on Polygonscan →
                  </a>
                </p>
              </div>
            ` : ''}
          </div>
          
          <div class="flex flex--gap-lg mt-2xl" style="justify-content: center;">
            <button class="btn btn--primary" onclick="router.navigate('/verify')">
              Verify Another
            </button>
            <button class="btn" onclick="router.navigate('/regulator')">
              Back to Dashboard
            </button>
          </div>
        </div>
      </main>
    </div>
  `;
}

// ============================================
// About Page
// ============================================
function renderAboutPage(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main class="section">
      <div class="container container--narrow">
        <h1 class="text-center mb-lg">About GSTchain</h1>
        <p class="text-center mb-2xl" style="color: #666;">
          A blockchain-powered GST invoice verification and fraud detection system.
        </p>
        
        <div class="card mb-xl">
          <h3 class="mb-md">The Problem</h3>
          <p>
            GST fraud through fake invoices and circular trading costs India billions annually. 
            Traditional systems lack the immutability and transparency needed to detect and prevent such fraud.
          </p>
        </div>
        
        <div class="card card--accent-yellow mb-xl">
          <h3 class="mb-md">Our Solution</h3>
          <p>
            GSTchain creates an immutable, tamper-proof record of every invoice by anchoring 
            cryptographic hashes to the Ethereum blockchain. Any modification to an invoice 
            is instantly detectable.
          </p>
        </div>
        
        <div class="card mb-xl">
          <h3 class="mb-lg">Technology Stack</h3>
          <div class="grid grid--2" style="gap: 16px;">
            <div>
              <strong>Blockchain</strong>
              <p style="color: #666; font-size: 0.9rem;">Ethereum (Sepolia testnet)</p>
            </div>
            <div>
              <strong>Encryption</strong>
              <p style="color: #666; font-size: 0.9rem;">AES-256-GCM</p>
            </div>
            <div>
              <strong>Hashing</strong>
              <p style="color: #666; font-size: 0.9rem;">SHA-256</p>
            </div>
            <div>
              <strong>Storage</strong>
              <p style="color: #666; font-size: 0.9rem;">Cloudflare R2</p>
            </div>
            <div>
              <strong>Database</strong>
              <p style="color: #666; font-size: 0.9rem;">PostgreSQL + Neo4j</p>
            </div>
            <div>
              <strong>Backend</strong>
              <p style="color: #666; font-size: 0.9rem;">FastAPI (Python)</p>
            </div>
          </div>
        </div>
        
        <div class="text-center">
          <button class="btn btn--primary btn--large" onclick="router.navigate('/select-role')">
            Get Started
          </button>
        </div>
      </div>
    </main>
    
    ${renderFooter()}
  `;
}

// ============================================
// 404 Page
// ============================================
function render404(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main class="section" style="min-height: 60vh; display: flex; align-items: center;">
      <div class="container text-center">
        <h1 style="font-size: 8rem; margin-bottom: 0;">404</h1>
        <h2 class="mb-lg">Page Not Found</h2>
        <p class="mb-xl" style="color: #666;">The page you're looking for doesn't exist or has been moved.</p>
        <button class="btn btn--primary" onclick="router.navigate('/')">
          Go Home
        </button>
      </div>
    </main>
    
    ${renderFooter()}
  `;
}

// ============================================
// Utility Functions
// ============================================
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    toast.success('Copied to clipboard!');
  }).catch(() => {
    toast.error('Failed to copy');
  });
}

// ============================================
// Fraud Detection Page
// ============================================
function renderFraudDetectionPage(container) {
  // Auth guard - redirect to login if not authenticated
  if (!state.isAuthenticated()) {
    toast.warning('Please login to access this page');
    router.navigate('/login/auditor');
    return;
  }

  container.innerHTML = `
    ${renderHeader()}
    
    <div class="dashboard">
      <aside class="dashboard__sidebar">
        <nav class="dashboard__nav">
          <div class="dashboard__nav-item" onclick="router.navigate('/regulator')">
            Dashboard
          </div>
          <div class="dashboard__nav-item" onclick="router.navigate('/verify')">
            Verify Invoice
          </div>
          <div class="dashboard__nav-item dashboard__nav-item--active">
            Cycle Detection
          </div>
        </nav>
      </aside>
      
      <main class="dashboard__main">
        <div class="dashboard__header">
          <h1 class="dashboard__title">Circular Trade Detection</h1>
          <p class="dashboard__subtitle">Detect suspicious circular invoice patterns and analyze fraud risk</p>
        </div>
        
        <div class="card mb-xl">
          <div class="flex flex--between" style="align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
              <h3>Cycle Analysis</h3>
              <p style="color: #666; font-size: 0.9rem;">Scan the invoice graph for circular trading patterns</p>
            </div>
            <button class="btn btn--primary" onclick="runFraudDetection()">
              Detect Cycles
            </button>
          </div>
        </div>
        
        <div class="card mb-xl card--accent-yellow">
          <h3 class="mb-md">Search GSTIN</h3>
          <p style="font-size: 0.9rem; margin-bottom: 16px;">Check if a specific GSTIN is involved in any invoices or suspicious patterns</p>
          <form onsubmit="searchGSTIN(event)" class="flex flex--gap-md" style="flex-wrap: wrap;">
            <input type="text" class="input" id="gstin-search" placeholder="Enter GSTIN e.g., 27ABCDE1234F1Z5" style="flex: 1; min-width: 250px;" required>
            <button type="submit" class="btn btn--primary">Search</button>
          </form>
          
          <div id="gstin-loading" class="hidden mt-lg">
            <div class="loading">
              <div class="loading__spinner"></div>
              <div class="loading__text">Searching...</div>
            </div>
          </div>
          
          <div id="gstin-results" class="hidden mt-lg"></div>
        </div>
        
        <div id="fraud-loading" class="hidden">
          <div class="loading">
            <div class="loading__spinner"></div>
            <div class="loading__text">Analyzing invoice graph...</div>
          </div>
        </div>
        
        <div id="fraud-results" class="hidden">
          <div class="stats-grid mb-xl">
            <div class="card stat-card card--accent-pink">
              <div class="stat-card__value" id="stat-cycles">0</div>
              <div class="stat-card__label">Cycles Detected</div>
            </div>
            <div class="card stat-card" style="background: #EF4444; color: white;">
              <div class="stat-card__value" id="stat-high-risk">0</div>
              <div class="stat-card__label">High Risk</div>
            </div>
            <div class="card stat-card card--accent-yellow">
              <div class="stat-card__value" id="stat-medium-risk">0</div>
              <div class="stat-card__label">Medium Risk</div>
            </div>
            <div class="card stat-card card--accent-green">
              <div class="stat-card__value" id="stat-value">₹0</div>
              <div class="stat-card__label">Value at Risk</div>
            </div>
          </div>
          
          <div id="cycles-list"></div>
        </div>
        
        <div class="card mt-xl">
          <h3 class="mb-lg">Fraud Detection Rules</h3>
          <div id="rules-list">
            <p style="color: #666;">Loading rules...</p>
          </div>
        </div>
      </main>
    </div>
  `;

  // Load rules on page load
  loadFraudRules();
}

async function runFraudDetection() {
  const loading = document.getElementById('fraud-loading');
  const results = document.getElementById('fraud-results');

  loading.classList.remove('hidden');
  results.classList.add('hidden');

  try {
    const data = await api.detectCycles();

    loading.classList.add('hidden');
    results.classList.remove('hidden');

    // Update stats
    document.getElementById('stat-cycles').textContent = data.cycles_detected;
    document.getElementById('stat-high-risk').textContent = data.summary.high_risk;
    document.getElementById('stat-medium-risk').textContent = data.summary.medium_risk;
    document.getElementById('stat-value').textContent = '₹' + (data.summary.total_value_at_risk / 100000).toFixed(1) + 'L';

    // Render cycles
    const cyclesList = document.getElementById('cycles-list');

    if (data.cycles.length === 0) {
      cyclesList.innerHTML = `
        <div class="card card--accent-green text-center">
          <h3>No Suspicious Cycles Detected</h3>
          <p>The invoice graph appears clean.</p>
        </div>
      `;
    } else {
      cyclesList.innerHTML = data.cycles.map(cycle => `
        <div class="card mb-lg ${cycle.risk_level === 'HIGH' ? 'card--accent-pink' : cycle.risk_level === 'MEDIUM' ? 'card--accent-yellow' : ''}">
          <div class="flex flex--between" style="align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div>
              <div class="flex flex--gap-md" style="align-items: center; margin-bottom: 8px;">
                <strong style="font-size: 1.25rem;">${cycle.cycle_id}</strong>
                <span class="badge badge--${cycle.risk_level === 'HIGH' ? 'error' : cycle.risk_level === 'MEDIUM' ? 'warning' : 'success'}">
                  ${cycle.risk_level} RISK
                </span>
              </div>
              <p style="font-size: 0.9rem; margin-bottom: 12px;">
                <strong>Entities:</strong> ${cycle.nodes.length} | 
                <strong>Invoices:</strong> ${cycle.invoice_count} | 
                <strong>Value:</strong> ₹${(cycle.total_value / 100000).toFixed(2)}L
              </p>
            </div>
            <div class="text-center" style="min-width: 100px;">
              <div style="font-size: 2.5rem; font-weight: bold; font-family: var(--font-display);">${cycle.risk_score}</div>
              <div style="font-size: 0.75rem; text-transform: uppercase;">Risk Score</div>
            </div>
          </div>
          
          <div style="margin-top: 16px;">
            <strong style="font-size: 0.8rem; text-transform: uppercase;">Cycle Path:</strong>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
              ${cycle.nodes.map((gstin, i) => `
                <span style="background: ${cycle.risk_level === 'HIGH' ? 'rgba(0,0,0,0.2)' : 'rgba(0,0,0,0.1)'}; padding: 4px 8px; font-family: monospace; font-size: 0.8rem; border-radius: 4px;">
                  ${gstin}
                </span>
                ${i < cycle.nodes.length - 1 ? '<span style="color: inherit;">→</span>' : '<span style="color: inherit;">↩</span>'}
              `).join('')}
            </div>
          </div>
          
          ${cycle.reasons.length > 0 ? `
            <div style="margin-top: 16px; padding-top: 16px; border-top: 2px solid rgba(0,0,0,0.1);">
              <strong style="font-size: 0.8rem; text-transform: uppercase;">Risk Factors:</strong>
              <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                ${cycle.reasons.map(r => `
                  <span class="badge" style="background: rgba(0,0,0,0.1); color: inherit;">
                    ${r.rule_id} (+${r.risk})
                  </span>
                `).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      `).join('');
    }

    if (data.status === 'demo_mode') {
      toast.warning('Showing demo data - Neo4j not connected');
    } else {
      toast.success(`Found ${data.cycles_detected} cycles`);
    }

  } catch (error) {
    loading.classList.add('hidden');
    toast.error('Fraud detection failed: ' + error.message);
  }
}

async function loadFraudRules() {
  try {
    const data = await api.getRiskRules();
    const rulesList = document.getElementById('rules-list');

    rulesList.innerHTML = data.rules.map(category => `
      <div style="margin-bottom: 24px;">
        <h4 style="margin-bottom: 12px; color: var(--color-primary);">${category.category} Rules</h4>
        <div style="display: grid; gap: 8px;">
          ${category.rules.map(rule => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--color-bg-alt); border: 2px solid var(--color-black);">
              <div>
                <strong style="font-family: monospace; font-size: 0.85rem;">${rule.id}</strong>
                <p style="margin: 4px 0 0; font-size: 0.85rem; color: #666;">${rule.description}</p>
              </div>
              <span class="badge ${rule.max_risk >= 80 ? 'badge--error' : rule.max_risk >= 50 ? 'badge--warning' : 'badge--info'}">
                Max +${rule.max_risk}
              </span>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');

  } catch (error) {
    document.getElementById('rules-list').innerHTML = '<p style="color: #666;">Could not load rules</p>';
  }
}

// View Invoice JSON function
async function viewInvoiceJSON(hash) {
  try {
    const modal = document.getElementById('invoice-json-modal');
    const content = document.getElementById('invoice-json-content');

    content.textContent = 'Loading...';
    modal.classList.remove('hidden');

    const data = await api.getInvoiceData(hash);

    if (data.error) {
      content.textContent = 'Error: ' + data.error;
    } else {
      content.textContent = JSON.stringify(data.invoice_data, null, 2);
    }
  } catch (error) {
    toast.error('Failed to load invoice: ' + error.message);
  }
}

// Search GSTIN function
async function searchGSTIN(e) {
  e.preventDefault();

  const gstin = document.getElementById('gstin-search').value.trim().toUpperCase();
  const loading = document.getElementById('gstin-loading');
  const results = document.getElementById('gstin-results');

  loading.classList.remove('hidden');
  results.classList.add('hidden');

  try {
    const data = await api.searchByGSTIN(gstin);

    loading.classList.add('hidden');
    results.classList.remove('hidden');

    if (data.total_invoices === 0) {
      results.innerHTML = `
        <div style="padding: 16px; background: white; border: 3px solid black;">
          <p><strong>GSTIN ${gstin}</strong> not found in the system.</p>
          <p style="color: #666; font-size: 0.9rem; margin-top: 8px;">This GSTIN has no recorded invoices.</p>
        </div>
      `;
    } else {
      results.innerHTML = `
        <div style="padding: 16px; background: white; border: 3px solid black;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h4>GSTIN: ${data.gstin}</h4>
            ${data.in_cycles ? '<span class="badge badge--error">IN CYCLE</span>' : '<span class="badge badge--success">CLEAN</span>'}
          </div>
          
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">
            <div style="text-align: center; padding: 12px; background: var(--color-primary); color: white;">
              <div style="font-size: 1.5rem; font-weight: bold;">${data.total_invoices}</div>
              <div style="font-size: 0.75rem; text-transform: uppercase;">Total Invoices</div>
            </div>
            <div style="text-align: center; padding: 12px; background: var(--color-accent-green); color: white;">
              <div style="font-size: 1.5rem; font-weight: bold;">${data.as_supplier}</div>
              <div style="font-size: 0.75rem; text-transform: uppercase;">As Supplier</div>
            </div>
            <div style="text-align: center; padding: 12px; background: var(--color-accent-cyan);">
              <div style="font-size: 1.5rem; font-weight: bold;">${data.as_recipient}</div>
              <div style="font-size: 0.75rem; text-transform: uppercase;">As Recipient</div>
            </div>
            <div style="text-align: center; padding: 12px; background: var(--color-accent-yellow);">
              <div style="font-size: 1.2rem; font-weight: bold;">₹${(data.total_value / 100000).toFixed(2)}L</div>
              <div style="font-size: 0.75rem; text-transform: uppercase;">Total Value</div>
            </div>
          </div>
          
          <h5 style="margin-bottom: 8px;">Invoices:</h5>
          <div style="max-height: 250px; overflow-y: auto;">
            ${data.invoices.map(inv => `
              <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee; gap: 8px;">
                <div style="flex: 1;">
                  <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <code style="font-size: 0.75rem;">${inv.invoice_hash ? inv.invoice_hash.slice(0, 16) + '...' : 'N/A'}</code>
                    <span class="badge" style="background: ${inv.role === 'supplier' ? 'var(--color-accent-green)' : 'var(--color-accent-cyan)'}; color: ${inv.role === 'supplier' ? 'white' : 'black'};">
                      ${inv.role}
                    </span>
                  </div>
                  <div style="font-size: 0.75rem; color: #666; margin-top: 4px;">
                    ${inv.counterparty ? '→ ' + inv.counterparty : ''} 
                    ${inv.amount ? ' | ₹' + inv.amount.toLocaleString() : ''}
                    ${inv.invoice_date ? ' | ' + inv.invoice_date : ''}
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    toast.success(`Found ${data.total_invoices} invoices for ${gstin}`);

  } catch (error) {
    loading.classList.add('hidden');
    results.classList.remove('hidden');
    results.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    toast.error('Search failed: ' + error.message);
  }
}

// View invoice from search results
async function viewInvoiceFromSearch(hash) {
  try {
    const data = await api.getInvoiceData(hash);

    if (data.error) {
      toast.error('Error: ' + data.error);
      return;
    }

    // Create a modal overlay
    const overlay = document.createElement('div');
    overlay.id = 'json-overlay';
    overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 20px;';
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

    overlay.innerHTML = `
      <div style="background: #1a1a1a; color: #22C55E; padding: 24px; max-width: 800px; max-height: 80vh; overflow: auto; border: 4px solid white;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 style="color: white; margin: 0;">Invoice Data</h3>
          <button onclick="document.getElementById('json-overlay').remove()" style="background: white; border: none; padding: 8px 16px; cursor: pointer; font-weight: bold;">✕ Close</button>
        </div>
        <div style="margin-bottom: 16px; color: #999;">
          <strong>Hash:</strong> ${data.invoice_hash}<br>
          <strong>Supplier:</strong> ${data.supplier_gstin}<br>
          <strong>Recipient:</strong> ${data.recipient_gstin}
        </div>
        <pre style="font-size: 0.8rem; overflow-x: auto;">${JSON.stringify(data.invoice_data, null, 2)}</pre>
      </div>
    `;

    document.body.appendChild(overlay);

  } catch (error) {
    toast.error('Failed to load: ' + error.message);
  }
}

// ============================================
// Login Pages
// ============================================
function renderBusinessLogin(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main class="section" style="min-height: 70vh; display: flex; align-items: center;">
      <div class="container container--narrow">
        <div class="card card--no-hover">
          <h2 class="text-center mb-lg">Business Login</h2>
          <p class="text-center mb-xl" style="color: #666;">Sign in to upload invoices and manage your proofs</p>
          
          <form id="login-form" onsubmit="handleBusinessLogin(event)">
            <div class="input-group mb-lg">
              <label class="input-label">Email</label>
              <input type="email" class="input" name="email" required placeholder="your@email.com">
            </div>
            <div class="input-group mb-xl">
              <label class="input-label">Password</label>
              <input type="password" class="input" name="password" required placeholder="Enter password">
            </div>
            <button type="submit" class="btn btn--primary btn--large" style="width: 100%;">Login</button>
          </form>
          
          <p class="text-center mt-xl" style="color: #666;">
            Don't have an account? 
            <a href="#/register/business" style="color: var(--color-primary); font-weight: 600;">Register here</a>
          </p>
        </div>
      </div>
    </main>
    
    ${renderFooter()}
  `;
}

function renderAuditorLogin(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main class="section" style="min-height: 70vh; display: flex; align-items: center;">
      <div class="container container--narrow">
        <div class="card card--no-hover">
          <h2 class="text-center mb-lg">Auditor Login</h2>
          <p class="text-center mb-xl" style="color: #666;">Sign in to verify invoices and detect fraud</p>
          
          <form id="login-form" onsubmit="handleAuditorLogin(event)">
            <div class="input-group mb-lg">
              <label class="input-label">Email</label>
              <input type="email" class="input" name="email" required placeholder="your@email.com">
            </div>
            <div class="input-group mb-xl">
              <label class="input-label">Password</label>
              <input type="password" class="input" name="password" required placeholder="Enter password">
            </div>
            <button type="submit" class="btn btn--primary btn--large" style="width: 100%;">Login</button>
          </form>
          
          <p class="text-center mt-xl" style="color: #666;">
            Don't have an account? 
            <a href="#/register/auditor" style="color: var(--color-primary); font-weight: 600;">Register here</a>
          </p>
        </div>
      </div>
    </main>
    
    ${renderFooter()}
  `;
}

// ============================================
// Register Pages
// ============================================
function renderBusinessRegister(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main class="section" style="min-height: 70vh; display: flex; align-items: center;">
      <div class="container container--narrow">
        <div class="card card--no-hover">
          <h2 class="text-center mb-lg">Business Registration</h2>
          <p class="text-center mb-xl" style="color: #666;">Create an account to start uploading invoices</p>
          
          <form id="register-form" onsubmit="handleBusinessRegister(event)">
            <div class="input-group mb-lg">
              <label class="input-label">Company Name</label>
              <input type="text" class="input" name="company_name" required placeholder="Your Company Ltd.">
            </div>
            <div class="input-group mb-lg">
              <label class="input-label">GSTIN</label>
              <input type="text" class="input" name="gstin" required placeholder="27ABCDE1234F1Z5">
            </div>
            <div class="input-group mb-lg">
              <label class="input-label">Email</label>
              <input type="email" class="input" name="email" required placeholder="your@email.com">
            </div>
            <div class="input-group mb-lg">
              <label class="input-label">Phone (Optional)</label>
              <input type="tel" class="input" name="phone" placeholder="+91 9876543210">
            </div>
            <div class="input-group mb-xl">
              <label class="input-label">Password</label>
              <input type="password" class="input" name="password" required minlength="6" placeholder="Min 6 characters">
            </div>
            <button type="submit" class="btn btn--primary btn--large" style="width: 100%;">Create Account</button>
          </form>
          
          <p class="text-center mt-xl" style="color: #666;">
            Already have an account? 
            <a href="#/login/business" style="color: var(--color-primary); font-weight: 600;">Login here</a>
          </p>
        </div>
      </div>
    </main>
    
    ${renderFooter()}
  `;
}

function renderAuditorRegister(container) {
  container.innerHTML = `
    ${renderHeader()}
    
    <main class="section" style="min-height: 70vh; display: flex; align-items: center;">
      <div class="container container--narrow">
        <div class="card card--no-hover">
          <h2 class="text-center mb-lg">Auditor Registration</h2>
          <p class="text-center mb-xl" style="color: #666;">Create an account to verify invoices</p>
          
          <form id="register-form" onsubmit="handleAuditorRegister(event)">
            <div class="input-group mb-lg">
              <label class="input-label">Full Name</label>
              <input type="text" class="input" name="full_name" required placeholder="Your Full Name">
            </div>
            <div class="input-group mb-lg">
              <label class="input-label">License Number</label>
              <input type="text" class="input" name="license_number" required placeholder="AUD-12345">
            </div>
            <div class="input-group mb-lg">
              <label class="input-label">Organization (Optional)</label>
              <input type="text" class="input" name="organization" placeholder="Your Organization">
            </div>
            <div class="input-group mb-lg">
              <label class="input-label">Email</label>
              <input type="email" class="input" name="email" required placeholder="your@email.com">
            </div>
            <div class="input-group mb-xl">
              <label class="input-label">Password</label>
              <input type="password" class="input" name="password" required minlength="6" placeholder="Min 6 characters">
            </div>
            <button type="submit" class="btn btn--primary btn--large" style="width: 100%;">Create Account</button>
          </form>
          
          <p class="text-center mt-xl" style="color: #666;">
            Already have an account? 
            <a href="#/login/auditor" style="color: var(--color-primary); font-weight: 600;">Login here</a>
          </p>
        </div>
      </div>
    </main>
    
    ${renderFooter()}
  `;
}

// ============================================
// Auth Handlers
// ============================================
async function handleBusinessLogin(e) {
  e.preventDefault();
  const form = e.target;
  const email = form.email.value;
  const password = form.password.value;

  try {
    const result = await api.loginBusiness({ email, password });
    if (state.login(result.access_token, { email: result.user_email, name: result.user_name }, 'business')) {
      toast.success('Login successful!');
      router.navigate('/business');
    }
  } catch (error) {
    toast.error(error.message);
  }
}

async function handleAuditorLogin(e) {
  e.preventDefault();
  const form = e.target;
  const email = form.email.value;
  const password = form.password.value;

  try {
    const result = await api.loginAuditor({ email, password });
    if (state.login(result.access_token, { email: result.user_email, name: result.user_name }, 'auditor')) {
      toast.success('Login successful!');
      router.navigate('/regulator');
    }
  } catch (error) {
    toast.error(error.message);
  }
}

async function handleBusinessRegister(e) {
  e.preventDefault();
  const form = e.target;
  const userData = {
    email: form.email.value,
    password: form.password.value,
    company_name: form.company_name.value,
    gstin: form.gstin.value,
    phone: form.phone.value || null
  };

  try {
    const result = await api.registerBusiness(userData);
    if (state.login(result.access_token, { email: result.user_email, name: result.user_name }, 'business')) {
      toast.success('Registration successful!');
      router.navigate('/business');
    }
  } catch (error) {
    toast.error(error.message);
  }
}

async function handleAuditorRegister(e) {
  e.preventDefault();
  const form = e.target;
  const userData = {
    email: form.email.value,
    password: form.password.value,
    full_name: form.full_name.value,
    license_number: form.license_number.value,
    organization: form.organization.value || null
  };

  try {
    const result = await api.registerAuditor(userData);
    if (state.login(result.access_token, { email: result.user_email, name: result.user_name }, 'auditor')) {
      toast.success('Registration successful!');
      router.navigate('/regulator');
    }
  } catch (error) {
    toast.error(error.message);
  }
}

function handleLogout() {
  // Close dropdown first
  const dropdown = document.getElementById('user-dropdown-menu');
  if (dropdown) dropdown.classList.add('hidden');

  state.logout();
  toast.success('Logged out successfully');
  router.navigate('/');
}

function toggleUserDropdown(e) {
  e.stopPropagation();
  const dropdown = document.getElementById('user-dropdown-menu');
  if (dropdown) {
    dropdown.classList.toggle('hidden');

    // Close dropdown when clicking outside
    if (!dropdown.classList.contains('hidden')) {
      const closeDropdown = (event) => {
        if (!event.target.closest('.user-dropdown')) {
          dropdown.classList.add('hidden');
          document.removeEventListener('click', closeDropdown);
        }
      };
      setTimeout(() => document.addEventListener('click', closeDropdown), 0);
    }
  }
}

// ============================================
// Route Registration
// ============================================
router.addRoute('/', renderLanding);
router.addRoute('/select-role', renderRoleSelection);
router.addRoute('/login/business', renderBusinessLogin);
router.addRoute('/login/auditor', renderAuditorLogin);
router.addRoute('/register/business', renderBusinessRegister);
router.addRoute('/register/auditor', renderAuditorRegister);
router.addRoute('/business', renderBusinessDashboard);
router.addRoute('/upload', renderUploadPage);
router.addRoute('/proof', renderProofPage);
router.addRoute('/regulator', renderRegulatorDashboard);
router.addRoute('/verify', renderVerifyPage);
router.addRoute('/verify-result', renderVerifyResultPage);
router.addRoute('/fraud-detection', renderFraudDetectionPage);
router.addRoute('/about', renderAboutPage);
router.addRoute('/404', render404);

// Handle dynamic routes
const originalNavigate = router.navigate.bind(router);
router.navigate = function (path) {
  // Handle /verify/:hash routes
  if (path.startsWith('/verify/') && path !== '/verify-result') {
    const hash = path.replace('/verify/', '');
    document.getElementById('app').innerHTML = '';
    renderVerifyPage(document.getElementById('app'));
    setTimeout(() => {
      const input = document.getElementById('verify-hash');
      if (input) {
        input.value = hash;
        document.getElementById('verify-form').dispatchEvent(new Event('submit'));
      }
    }, 100);
    return;
  }
  originalNavigate(path);
};

// Initialize state from local storage
state.init();

// Start the application
router.start();

// ============================================
// Expose functions to global scope for onclick handlers
// ============================================
window.router = router;
window.selectRole = selectRole;
window.handleDragOver = handleDragOver;
window.handleDragLeave = handleDragLeave;
window.handleDrop = handleDrop;
window.handleFileSelect = handleFileSelect;
window.handleFile = handleFile;
window.clearFile = clearFile;
window.handleManualSubmit = handleManualSubmit;
window.downloadProof = downloadProof;
window.quickVerify = quickVerify;
window.performVerification = performVerification;
window.copyToClipboard = copyToClipboard;
window.runFraudDetection = runFraudDetection;
window.loadFraudRules = loadFraudRules;
window.viewInvoiceJSON = viewInvoiceJSON;
window.searchGSTIN = searchGSTIN;
window.viewInvoiceFromSearch = viewInvoiceFromSearch;

// Auth handlers
window.handleBusinessLogin = handleBusinessLogin;
window.handleAuditorLogin = handleAuditorLogin;
window.handleBusinessRegister = handleBusinessRegister;
window.handleAuditorRegister = handleAuditorRegister;
window.handleLogout = handleLogout;
window.handleLogout = handleLogout;
window.toggleUserDropdown = toggleUserDropdown;
window.switchAccount = (index) => state.switchAccount(index);

console.log('GSTchain Frontend Loaded');

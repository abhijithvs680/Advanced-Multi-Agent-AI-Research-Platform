import { NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Briefcase,
    PlusCircle,
    Settings,
    Activity,
    ChevronLeft
} from 'lucide-react';
import './Sidebar.css';

interface NavItem {
    path: string;
    label: string;
    icon: React.ReactNode;
}

const navItems: NavItem[] = [
    { path: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/jobs', label: 'Jobs', icon: <Briefcase size={20} /> },
    { path: '/create-job', label: 'Create Job', icon: <PlusCircle size={20} /> },
    { path: '/settings', label: 'Settings', icon: <Settings size={20} /> },
];

interface SidebarProps {
    collapsed?: boolean;
    onToggle?: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
    const location = useLocation();

    return (
        <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
            {/* Logo */}
            <div className="sidebar-header">
                <div className="logo">
                    <div className="logo-icon">
                        <img src="/vite.svg" alt="Platform Logo" style={{ width: 32, height: 32 }} />
                    </div>
                    {!collapsed && (
                        <div className="logo-text">
                            <span className="logo-title">Research</span>
                            <span className="logo-subtitle">Platform</span>
                        </div>
                    )}
                </div>
                <button className="collapse-btn" onClick={onToggle}>
                    <ChevronLeft size={18} />
                </button>
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `nav-item ${isActive ? 'active' : ''}`
                        }
                    >
                        <span className="nav-icon">{item.icon}</span>
                        {!collapsed && <span className="nav-label">{item.label}</span>}
                    </NavLink>
                ))}
            </nav>

            {/* Status Footer */}
            <div className="sidebar-footer">
                <div className="status-indicator">
                    <Activity size={16} className="status-icon" />
                    {!collapsed && <span>System Active</span>}
                </div>
            </div>
        </aside>
    );
}

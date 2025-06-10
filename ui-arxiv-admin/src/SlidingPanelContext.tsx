import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

interface SlidingPanelContextType {
    isPanelOpen: boolean;
    togglePanel: () => void;
    openPanel: () => void;
    closePanel: () => void;
}

const SlidingPanelContext = createContext<SlidingPanelContextType | undefined>(undefined);

interface SlidingPanelProviderProps {
    children: ReactNode;
}

export const SlidingPanelProvider: React.FC<SlidingPanelProviderProps> = ({ children }) => {
    const [isPanelOpen, setIsPanelOpen] = useState(false);

    const togglePanel = () => setIsPanelOpen(prev => !prev);
    const openPanel = () => setIsPanelOpen(true);
    const closePanel = () => setIsPanelOpen(false);

    // Add keyboard shortcut listener
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            // Check for Ctrl+L (Windows/Linux) or Cmd+L (Mac)
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'l') {
                event.preventDefault(); // Prevent browser's default behavior (focus address bar)
                togglePanel();
            }
        };

        // Add event listener
        document.addEventListener('keydown', handleKeyDown);

        // Cleanup event listener on unmount
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, []); // Empty dependency array since togglePanel is stable

    return (
        <SlidingPanelContext.Provider value={{ isPanelOpen, togglePanel, openPanel, closePanel }}>
            {children}
        </SlidingPanelContext.Provider>
    );
};

export const useSlidingPanel = () => {
    const context = useContext(SlidingPanelContext);
    if (context === undefined) {
        throw new Error('useSlidingPanel must be used within a SlidingPanelProvider');
    }
    return context;
};

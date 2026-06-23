import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Github, Command, ArrowRight } from 'lucide-react';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen w-full bg-[#0a0a0c] text-white overflow-hidden relative font-sans flex flex-col">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-accent/20 blur-[120px] mix-blend-screen" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent/10 blur-[120px] mix-blend-screen" />
        {/* Subtle grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.03]" 
          style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 w-full max-w-7xl mx-auto">
        <div className="flex items-center gap-2 text-white font-semibold text-lg tracking-tight">
          <Command className="w-6 h-6 text-accent" />
          <span>CodeSense AI</span>
        </div>
        <div className="flex items-center gap-4">
          <a href="#" className="text-gray-400 hover:text-white transition-colors p-2 bg-white/5 rounded-md hover:bg-white/10 border border-white/5">
            <Github className="w-5 h-5" />
          </a>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto text-center w-full mt-[-5vh]">
        
        {/* Badge */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/30 text-accent text-xs font-semibold tracking-widest uppercase shadow-[0_0_15px_rgba(92,103,255,0.2)]"
        >
          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          RAG Powered
        </motion.div>

        {/* Hero Heading */}
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight mb-6"
          style={{
            backgroundImage: 'linear-gradient(to bottom, #ffffff, #9ca3af)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          CodeSense AI
        </motion.h1>

        {/* Subheading */}
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-lg sm:text-xl text-gray-400 mb-12 max-w-2xl leading-relaxed"
        >
          Understand any codebase instantly using AI-powered retrieval and semantic search.
        </motion.p>

        {/* Try It Out Box */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="w-full max-w-md group"
        >
          <div className="relative p-[1px] rounded-2xl bg-gradient-to-b from-white/10 to-transparent hover:from-accent/50 transition-colors duration-500">
            <div className="absolute inset-0 bg-accent/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl" />
            <div className="relative bg-[#121318]/90 backdrop-blur-xl border border-white/5 p-8 rounded-2xl flex flex-col items-center gap-6 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              <h3 className="text-xl font-medium text-gray-200">Ready to explore?</h3>
              
              <button 
                onClick={() => navigate('/auth')}
                className="w-full relative flex items-center justify-center gap-2 bg-accent hover:bg-[#4b54db] text-white py-4 px-8 rounded-xl font-medium transition-all duration-300 transform active:scale-95 group/btn overflow-hidden"
              >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300 ease-out" />
                <span className="relative">Try It Out</span>
                <ArrowRight className="w-5 h-5 relative group-hover/btn:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </motion.div>

      </main>
      
      {/* Footer minimal */}
      <footer className="relative z-10 py-6 text-center text-gray-600 text-sm">
        &copy; {new Date().getFullYear()} CodeSense AI. All rights reserved.
      </footer>
    </div>
  );
};

export default Landing;

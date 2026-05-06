'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { FileText, Shield, Zap, ArrowRight } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-purple-900/20">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto"
        >
          <h1 className="text-6xl md:text-7xl font-bold mb-6">
            <span className="text-gradient">Save 70%+ Time</span>
            <br />
            <span className="text-white">on Document Review</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-8">
            AI-powered GST invoice & contract analysis for Indian SMEs.
            <br />
            Zero cost. 100% private. Production-ready.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register" className="glass-button flex items-center gap-2">
              Get Started Free <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="/login" className="glass-button-secondary">
              Sign In
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid md:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card"
          >
            <FileText className="w-12 h-12 text-cyan-400 mb-4" />
            <h3 className="text-2xl font-bold mb-2">GST Auto-Detection</h3>
            <p className="text-gray-400">
              Automatically extracts GSTIN, HSN codes, and tax breakdowns from invoices
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-card"
          >
            <Shield className="w-12 h-12 text-purple-400 mb-4" />
            <h3 className="text-2xl font-bold mb-2">Legal Risk Flags</h3>
            <p className="text-gray-400">
              Identifies penalty clauses, Force Majeure, and compliance gaps automatically
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="glass-card"
          >
            <Zap className="w-12 h-12 text-pink-400 mb-4" />
            <h3 className="text-2xl font-bold mb-2">100% Local & Private</h3>
            <p className="text-gray-400">
              Runs entirely on your machine. No API costs. No data leaves your system.
            </p>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8 }}
          className="glass-neon rounded-3xl p-12 max-w-3xl mx-auto"
        >
          <h2 className="text-4xl font-bold mb-4">Ready to Save Lakhs Every Month?</h2>
          <p className="text-xl text-gray-300 mb-8">
            Join Indian SMEs using AI to review documents faster and stay compliant.
          </p>
          <Link href="/register" className="glass-button text-lg">
            Start Free Trial <ArrowRight className="w-5 h-5 ml-2" />
          </Link>
        </motion.div>
      </section>
    </div>
  );
}

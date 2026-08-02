"use client";

import { BusinessForm } from "@/components/business/business-form";

export default function BusinessPage() {
  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Business Profile</h1>
        <p className="text-slate-400 mt-1">
          Set up your business to get personalized AI guidance.
        </p>
      </div>
      <BusinessForm />
    </div>
  );
}

'use client';

export default function ProgressTracker() {
  const steps = ['Upload', 'Profile', 'Analyze', 'Visualize', 'Report'];
  const currentStep = 0;

  return (
    <div className="w-full">
      <div className="flex justify-between mb-8">
        {steps.map((step, index) => (
          <div
            key={step}
            className={`flex-1 text-center ${
              index <= currentStep ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            <div className="text-lg font-semibold">{step}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

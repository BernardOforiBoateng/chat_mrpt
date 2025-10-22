import React, { useState } from 'react';
import MethodCard from './MethodCard';

interface AnalysisData {
  pca?: {
    score: number;
    ranking: number;
    totalRanked: number;
    indicators: string[];
  };
  composite?: {
    score: number;
    ranking: number;
    totalRanked: number;
    indicators: string[];
  };
}

interface DualMethodDisplayProps {
  data: AnalysisData;
  wardName?: string;
  stateName?: string;
}

const DualMethodDisplay: React.FC<DualMethodDisplayProps> = ({
  data,
  wardName,
  stateName,
}) => {
  const [activeMethod, setActiveMethod] = useState<'PCA' | 'Composite' | null>(null);
  
  return (
    <div className="w-full">
      {/* Header */}
      {(wardName || stateName) && (
        <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Analysis Results
          </h2>
          <div className="flex items-center mt-1 text-sm text-gray-600">
            {wardName && (
              <>
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="font-medium">{wardName}</span>
                {stateName && <span className="mx-2">•</span>}
              </>
            )}
            {stateName && <span>{stateName}</span>}
          </div>
        </div>
      )}
      
      {/* Method Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MethodCard
          methodName="PCA"
          score={data.pca?.score}
          ranking={data.pca?.ranking}
          totalRanked={data.pca?.totalRanked}
          description="Principal Component Analysis reduces multiple indicators into key components that explain the most variance in malaria risk."
          indicators={data.pca?.indicators || [
            'Population density',
            'Healthcare accessibility',
            'Environmental factors',
            'Socioeconomic indicators',
            'Previous intervention coverage'
          ]}
          isActive={activeMethod === 'PCA'}
          onClick={() => setActiveMethod(activeMethod === 'PCA' ? null : 'PCA')}
        />
        
        <MethodCard
          methodName="Composite"
          score={data.composite?.score}
          ranking={data.composite?.ranking}
          totalRanked={data.composite?.totalRanked}
          description="Composite scoring combines weighted indicators to create a comprehensive risk assessment based on expert-defined criteria."
          indicators={data.composite?.indicators || [
            'Malaria incidence rate',
            'Intervention coverage gaps',
            'Vulnerability index',
            'Resource allocation efficiency',
            'Community readiness score'
          ]}
          isActive={activeMethod === 'Composite'}
          onClick={() => setActiveMethod(activeMethod === 'Composite' ? null : 'Composite')}
        />
      </div>
      
      {/* Comparison Summary */}
      {data.pca && data.composite && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Method Comparison</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Score Difference:</span>
              <span className="ml-2 font-medium">
                {Math.abs(data.pca.score - data.composite.score).toFixed(2)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Ranking Difference:</span>
              <span className="ml-2 font-medium">
                {Math.abs(data.pca.ranking - data.composite.ranking)} positions
              </span>
            </div>
          </div>
          {Math.abs(data.pca.ranking - data.composite.ranking) > 10 && (
            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
              <p className="text-xs text-yellow-800">
                ⚠️ Significant ranking difference detected. Consider reviewing both methodologies for this ward.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DualMethodDisplay;
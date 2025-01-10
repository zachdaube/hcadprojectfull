import React, { useState } from 'react';

const PropertySearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/search?query=${encodeURIComponent(searchQuery)}`);
      if (!response.ok) {
        throw new Error('Search failed');
      }
      const data = await response.json();
      console.log('Search results:', data);
      setSearchResults(data);
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to search properties');
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePropertySelect = async (accountNumber) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/property/${accountNumber}`);
      if (!response.ok) {
        throw new Error('Failed to fetch property details');
      }
      const data = await response.json();
      console.log('Property analysis:', data);
      setSelectedProperty(data);
    } catch (err) {
      console.error('Analysis error:', err);
      setError('Failed to fetch property details');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container mx-auto p-8 min-h-screen">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-400 to-blue-800 opacity-10"></div>
      
      <h1 className="text-4xl font-bold mb-8 text-center text-white">
        Property Tax Protest Helper
      </h1>

      {/* Search Section */}
      <div className="max-w-md mx-auto mb-8">
        <div className="flex space-x-2 mb-4">
          <input
            type="text"
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
            placeholder="Enter property address"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && !selectedProperty && (
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-white">Search Results</h2>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-600">
                  <th className="text-left p-4 text-gray-300">Address</th>
                  <th className="text-left p-4 text-gray-300">Built</th>
                  <th className="text-left p-4 text-gray-300">CDU</th>
                  <th className="text-left p-4 text-gray-300">Grade</th>
                  <th className="text-left p-4 text-gray-300">Building Area</th>
                  <th className="text-left p-4 text-gray-300">Total Value</th>
                  <th className="text-left p-4"></th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((property) => (
                  <tr key={property.account_number} className="border-b border-gray-700 hover:bg-gray-800/30">
                    <td className="p-4 text-gray-200">{property.street_address}</td>
                    <td className="p-4 text-gray-200">{property.year_built}</td>
                    <td className="p-4 text-gray-200">{property.cdu?.toFixed(2)}</td>
                    <td className="p-4 text-gray-200">{property.grade}</td>
                    <td className="p-4 text-gray-200">{property.building_area?.toLocaleString()} sq ft</td>
                    <td className="p-4 text-gray-200">${property.total_appraised_value?.toLocaleString()}</td>
                    <td className="p-4">
                      <button 
                        onClick={() => handlePropertySelect(property.account_number)}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        Get Comparables
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Selected Property Analysis */}
      {selectedProperty && (
        <div className="space-y-8">
          {/* Property Info */}
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4 text-white">Selected Property</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-gray-400">Address:</p>
                <p className="font-medium text-white">{selectedProperty.reference_property.street_address}</p>
              </div>
              <div>
                <p className="text-gray-400">Building Area:</p>
                <p className="font-medium text-white">
                  {selectedProperty.reference_property.building_area?.toLocaleString()} sq ft
                </p>
              </div>
              <div>
                <p className="text-gray-400">Current Appraised Value:</p>
                <p className="font-medium text-white">
                  ${selectedProperty.reference_property.total_appraised_value?.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-gray-400">Year Built:</p>
                <p className="font-medium text-white">{selectedProperty.reference_property.year_built}</p>
              </div>
              <div>
                <p className="text-gray-400">Grade:</p>
                <p className="font-medium text-white">{selectedProperty.reference_property.grade}</p>
              </div>
              <div>
                <p className="text-gray-400">CDU:</p>
                <p className="font-medium text-white">{selectedProperty.reference_property.cdu?.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-400">Number of Comparables Found:</p>
                <p className="font-medium text-white">{selectedProperty.num_comps_found}</p>
              </div>
            </div>
          </div>

          {/* Comparable Properties */}
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4 text-white">Five Most Comparable Properties</h2>
            <div className="overflow-x-auto mb-6">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-600">
                    <th className="text-left p-4 text-gray-300">Address</th>
                    <th className="text-left p-4 text-gray-300">Built</th>
                    <th className="text-left p-4 text-gray-300">CDU</th>
                    <th className="text-left p-4 text-gray-300">Grade</th>
                    <th className="text-left p-4 text-gray-300">Building Area</th>
                    <th className="text-left p-4 text-gray-300">Building Value</th>
                    <th className="text-left p-4 text-gray-300">Xtra Features</th>
                    <th className="text-left p-4 text-gray-300">Adjusted Building Value</th>
                    <th className="text-left p-4 text-gray-300">Adj Price per SqFt</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedProperty.value_analysis.lowest_five_comps.map((comp) => {
                    const fullCompData = selectedProperty.comparable_properties.find(
                      p => p.account_number === comp.account_number
                    );
                    return (
                      <tr key={comp.account_number} className="border-b border-gray-700 hover:bg-gray-800/30">
                        <td className="p-4 text-gray-200">{comp.street_address}</td>
                        <td className="p-4 text-gray-200">{fullCompData?.year_built}</td>
                        <td className="p-4 text-gray-200">{fullCompData?.cdu?.toFixed(2)}</td>
                        <td className="p-4 text-gray-200">{fullCompData?.grade}</td>
                        <td className="p-4 text-gray-200">{fullCompData?.building_area?.toLocaleString()} sq ft</td>
                        <td className="p-4 text-gray-200">${fullCompData?.building_value?.toLocaleString()}</td>
                        <td className="p-4 text-gray-200">${fullCompData?.extra_features_value?.toLocaleString()}</td>
                        <td className="p-4 text-gray-200">${comp.cdu_adjusted_value?.toLocaleString()}</td>
                        <td className="p-4 text-gray-200">${comp.price_per_sqft?.toLocaleString()}/sqft</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Value Analysis */}
            <div className="bg-gray-800/50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold mb-4 text-white">Value Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-gray-400">Median Price per SqFt:</p>
                  <p className="text-lg font-semibold text-white">
                    ${selectedProperty.value_analysis.median_price_per_sqft?.toLocaleString()}/sqft
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Suggested Market Value:</p>
                  <p className="text-lg font-semibold text-white">
                    ${selectedProperty.value_analysis.final_adjusted_value?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Current Appraised Value:</p>
                  <p className="text-lg font-semibold text-white">
                    ${selectedProperty.reference_property.total_appraised_value?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Potential Reduction:</p>
                  <p className="text-lg font-semibold text-green-400">
                    ${Math.max(0, 
                      selectedProperty.reference_property.total_appraised_value - 
                      selectedProperty.value_analysis.final_adjusted_value
                    )?.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <button 
              onClick={() => {
                setSelectedProperty(null);
                setSearchResults([]);
                setSearchQuery('');
              }}
              className="px-6 py-2 border border-gray-300 text-white rounded-lg hover:bg-gray-100/10"
            >
              Start New Search
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="text-red-500 text-center mt-4">
          {error}
        </div>
      )}
    </main>
  );
};

export default PropertySearch;
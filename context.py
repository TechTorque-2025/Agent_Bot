#contexxt.py
"""
Sample script to populate the TechTorque knowledge base with sample documents
Run this after starting the unified AI Agent service to create initial knowledge base
"""
import requests
import sys

# FIX: Update BASE_URL to match the new router prefix you chose in main.py
# Your router prefix is "/api/v1/ai"
BASE_URL = "http://localhost:8091/api/v1/ai"

# Sample documents covering various aspects of TechTorque services
SAMPLE_DOCUMENTS = [
    {
        "title": "Oil Change Service Details",
        "content": """Our oil change service includes replacement of engine oil with your choice of conventional,
        synthetic blend, or full synthetic oil. We replace the oil filter with a high-quality filter, check and
        top off all fluid levels including coolant, brake fluid, power steering, and windshield washer fluid.
        We also perform a 21-point inspection covering lights, wipers, belts, hoses, tire pressure, and battery.
        Service typically takes 30 minutes. We recommend oil changes every 5,000 miles for conventional oil or
        7,500 miles for synthetic oil.""",
        "doc_type": "service",
        "source": "service_catalog"
    },
    {
        "title": "Brake Service Information",
        "content": """Complete brake service includes inspection of brake pads, rotors, calipers, and brake lines.
        We replace worn brake pads with premium quality pads, resurface or replace rotors as needed, and perform
        brake fluid flush if necessary. All brake services include caliper lubrication and hardware replacement.
        We use ceramic brake pads for reduced noise and dust. Service typically takes 1-2 hours depending on
        vehicle condition. Signs you need brake service: squealing noise, grinding sounds, vibration when braking,
        or brake warning light.""",
        "doc_type": "service",
        "source": "service_catalog"
    },
    {
        "title": "Tire Services",
        "content": """We offer comprehensive tire services including tire rotation, balancing, wheel alignment,
        and tire replacement. Tire rotation should be performed every 6 months or 6,000-8,000 miles to ensure
        even wear. Wheel alignment corrects suspension angles and prevents uneven tire wear. We use computerized
        alignment equipment for precision. Signs you need alignment: vehicle pulls to one side, uneven tire wear,
        or steering wheel vibration. We carry major tire brands including Michelin, Goodyear, Bridgestone, and
        Continental.""",
        "doc_type": "service",
        "source": "service_catalog"
    },
    {
        "title": "Battery Service and Testing",
        "content": """Free battery testing available during any service visit. We use advanced diagnostic equipment
        to test battery health, charging system, and alternator output. Battery replacement includes testing the
        new battery, cleaning terminals, and checking charging system. Most batteries last 3-5 years depending on
        climate and driving conditions. Signs of battery problems: slow engine cranking, dimming lights, electrical
        issues, or battery warning light. We stock batteries for all vehicle makes and models.""",
        "doc_type": "service",
        "source": "service_catalog"
    },
    {
        "title": "AC Service and Repair",
        "content": """Air conditioning service includes system inspection, refrigerant level check, leak detection,
        and AC performance testing. We evacuate and recharge AC systems using environmentally-safe refrigerant.
        Common AC issues include refrigerant leaks, compressor failure, and electrical problems. Service includes
        checking all AC components: compressor, condenser, evaporator, and expansion valve. We recommend AC service
        every 2 years or if you notice reduced cooling, unusual noises, or bad odors from vents.""",
        "doc_type": "service",
        "source": "service_catalog"
    },
    {
        "title": "Business Hours and Location",
        "content": """TechTorque Auto Service Center is conveniently located at 123 Main Street in downtown.
        Our service hours are Monday through Friday 8:00 AM to 6:00 PM, and Saturday 9:00 AM to 4:00 PM.
        We are closed on Sundays. Walk-in customers are welcome, but appointments are recommended to minimize
        wait time. You can book appointments online through our website, by calling us, or using our mobile app.
        Free WiFi and comfortable waiting area available. Coffee and snacks provided for waiting customers.""",
        "doc_type": "general",
        "source": "business_info"
    },
    {
        "title": "Warranty and Guarantee",
        "content": """All repairs and services come with our comprehensive warranty. Labor is covered for 12 months
        or 12,000 miles, whichever comes first. Parts are covered for the warranty period specified by the
        manufacturer, typically 12-24 months. We stand behind our work and will re-perform any service that fails
        due to workmanship issues at no charge. Our warranty is honored at any TechTorque location nationwide.
        Keep your service records for warranty claims. Warranty does not cover damage from accidents, neglect,
        or normal wear and tear.""",
        "doc_type": "policy",
        "source": "warranty_policy"
    },
    {
        "title": "Payment and Pricing",
        "content": """We accept all major credit cards, debit cards, cash, and checks. We also offer financing
        through our partner for repairs over $500. Standard pricing: Oil change from $49.99, brake service
        $199-$399, tire rotation $29.99, wheel alignment $79.99, battery replacement $129-$199, AC service $149.99.
        Actual prices may vary based on vehicle make, model, and year. We provide written estimates before
        performing any work. Senior citizens and military personnel receive 10% discount. Ask about our loyalty
        program - earn points toward free services.""",
        "doc_type": "pricing",
        "source": "pricing_info"
    },
    {
        "title": "Appointment and Cancellation Policy",
        "content": """Appointments can be scheduled online, by phone, or through our mobile app. We recommend
        scheduling at least 24 hours in advance, especially for complex services. If you need to cancel or
        reschedule, please notify us at least 24 hours before your appointment time. Same-day cancellations
        may incur a $25 service fee. We understand emergencies happen - call us to discuss your situation.
        For urgent issues, we accommodate walk-ins based on technician availability. No-show appointments
        may require prepayment for future bookings.""",
        "doc_type": "policy",
        "source": "appointment_policy"
    },
    {
        "title": "Vehicle Drop-off and Loaner Cars",
        "content": """We offer convenient early bird drop-off service - drop your keys in our secure drop box
        before we open. Free loaner vehicles available for services expected to take more than 2 hours. Loaner
        cars are subject to availability and require a valid driver's license and insurance. Alternatively,
        we offer free shuttle service within 5 miles of our location during business hours. For longer repairs,
        we partner with local rental car companies to provide discounted rates. Call ahead to reserve a loaner
        vehicle.""",
        "doc_type": "general",
        "source": "convenience_services"
    },
    {
        "title": "Frequently Asked Questions",
        "content": """Q: Do you work on all vehicle makes? A: Yes, we service all domestic and import vehicles
        including cars, trucks, and SUVs. Q: Do you use original equipment (OEM) parts? A: We offer both OEM
        and high-quality aftermarket parts - you choose based on your budget. Q: Can I wait while my car is
        serviced? A: Yes, we have a comfortable waiting area with WiFi and refreshments. Q: Do you accept
        extended warranties? A: We work with most extended warranty providers. Q: Are your technicians certified?
        A: All technicians are ASE certified and receive ongoing training. Q: Do you provide vehicle inspections?
        A: Yes, we offer pre-purchase inspections and state safety inspections.""",
        "doc_type": "faq",
        "source": "customer_faq"
    },
    {
        "title": "Maintenance Schedule Recommendations",
        "content": """Following the manufacturer's recommended maintenance schedule helps prevent breakdowns and
        extends vehicle life. Key intervals: Every 5,000 miles - oil change and tire rotation. Every 15,000 miles -
        cabin air filter. Every 30,000 miles - engine air filter, fuel filter, transmission fluid. Every 60,000 miles -
        spark plugs (conventional), coolant flush. Every 100,000 miles - timing belt (if equipped). These are general
        guidelines - consult your owner's manual for specific requirements. We'll create a customized maintenance
        plan based on your vehicle, driving conditions, and mileage.""",
        "doc_type": "guide",
        "source": "maintenance_guide"
    },
    {
        "title": "Warning Signs and When to Seek Service",
        "content": """Warning signs requiring immediate attention: Check engine light, brake warning light,
        oil pressure warning light, temperature warning light, unusual noises (grinding, squealing, knocking),
        fluid leaks under vehicle, smoke from engine or exhaust, strong burning smell, vibration or pulling
        while driving. Don't ignore warning lights - they indicate issues that can worsen quickly. Schedule
        service immediately if you experience any of these symptoms. For emergency situations like overheating
        or loss of brakes, pull over safely and call for towing assistance.""",
        "doc_type": "guide",
        "source": "diagnostic_guide"
    },
    {
        "title": "Insurance and Claims Process",
        "content": """We work directly with insurance companies for accident repairs and covered services. We can
        submit estimates and documentation to your insurance provider. Most insurance companies allow you to
        choose your repair shop - you're not required to use their preferred provider. We accept insurance
        assignments and can handle the claims process for you. For warranty claims on extended warranties, bring
        your warranty contract and we'll verify coverage before starting work. We provide detailed itemized
        invoices for insurance reimbursement.""",
        "doc_type": "policy",
        "source": "insurance_info"
    },
    {
        "title": "Seasonal Maintenance Tips",
        "content": """Prepare your vehicle for seasonal changes. Winter preparation: Check battery, test antifreeze
        protection, inspect belts and hoses, check tire tread and pressure, replace wiper blades, keep washer
        fluid full. Summer preparation: Check AC system, inspect cooling system, check tire pressure (increases
        in heat), verify all lights work. Spring/Fall: Good time for oil changes, tire rotation, and general
        inspection. Extreme temperatures stress vehicle systems - preventive maintenance prevents breakdowns
        during harsh weather.""",
        "doc_type": "guide",
        "source": "seasonal_guide"
    }
]


def check_service_health():
    """Check if the chatbot service is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Service is healthy: {data.get('service')}")
            print(f"  Model: {data.get('model')}")
            print(f"  RAG Enabled: {data.get('rag_enabled', False)}")
            return True
        else:
            print(f"✗ Service returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to service: {e}")
        print(f"  Make sure the service is running on {BASE_URL}")
        return False


def get_rag_status():
    """Get detailed RAG system status"""
    try:
        response = requests.get(f"{BASE_URL}/rag/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\nRAG System Status:")
            print(f"  Available: {data.get('rag_available', False)}")

            embedding = data.get('embedding_service', {})
            print(f"  Embedding Model: {embedding.get('model_name')}")
            print(f"  Embedding Dimension: {embedding.get('dimension')}")

            vector_store = data.get('vector_store', {})
            print(f"  Vector Store: {vector_store.get('available', False)}")
            print(f"  Total Vectors: {vector_store.get('total_vectors', 0)}")
            print(f"  Index Name: {vector_store.get('index_name', 'N/A')}")
            return True
        else:
            print(f"✗ Could not get RAG status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error getting RAG status: {e}")
        return False


def ingest_documents():
    """Ingest sample documents into the knowledge base"""
    print(f"\n{'='*60}")
    # FIX: Correct the f-string inside the print call
    print(f"Ingesting {len(SAMPLE_DOCUMENTS)} documents into knowledge base...") 
    print(f"{'='*60}\n")

    try:
        # FIX: Changed endpoint to match your routes/chatAgent.py (documents/batch-ingest)
        response = requests.post(
            f"{BASE_URL}/documents/batch-ingest",
            json=SAMPLE_DOCUMENTS,
            timeout=120  # Allow up to 2 minutes for ingestion
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Batch ingestion completed!")
            print(f"  Total documents: {data.get('total')}")
            print(f"  Successfully ingested: {data.get('successful')}")
            print(f"  Failed: {data.get('failed')}")

            # Show details of ingested documents
            if data.get('successful', 0) > 0:
                print(f"\n{'='*60}")
                print("Ingested Documents:")
                print(f"{'='*60}")
                for i, result in enumerate(data.get('results', []), 1):
                    if result.get('success'):
                        print(f"\n{i}. {result.get('title')}")
                        print(f"   Doc ID: {result.get('doc_id')}")
                        print(f"   Chunks: {result.get('chunks_created')}")

            return True
        else:
            print(f"✗ Ingestion failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Error during ingestion: {e}")
        return False


def test_query():
    """Test the chatbot with a sample query"""
    print(f"\n{'='*60}")
    print("Testing chatbot with RAG-enhanced query...")
    print(f"{'='*60}\n")

    test_message = "What services do you offer for brake repair?"

    try:
        # FIX: Changed endpoint to match your routes/chatAgent.py (/chat)
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": test_message,
                "include_availability": False
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"Query: {test_message}")
            print(f"\nResponse:\n{data.get('reply')}") # FIX: Response field name is 'reply' in your ChatResponse model
            print(f"\nTimestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"✗ Query failed with status code: {response.status_code}")
            print(f"  Response: {response.text}") # Added response text for better debugging
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Error during query: {e}")
        return False


def main():
    """Main function to populate knowledge base"""
    print(f"\n{'='*60}")
    print("TechTorque Knowledge Base Population Script")
    print(f"{'='*60}\n")

    # Step 1: Check service health
    print("Step 1: Checking service health...")
    if not check_service_health():
        print("\n❌ Service is not available. Please start the unified AI Agent service first:")
        print("   python main.py") # Simpler instruction for running the service
        sys.exit(1)

    # Step 2: Get RAG status
    print("\nStep 2: Checking RAG system status...")
    if not get_rag_status():
        print("\n⚠️  Warning: RAG system may not be fully configured.")
        print("   Check your .env file for PINECONE_API_KEY and GOOGLE_API_KEY")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Step 3: Ingest documents
    print("\nStep 3: Ingesting documents...")
    if not ingest_documents():
        print("\n❌ Document ingestion failed.")
        sys.exit(1)

    # Step 4: Verify with RAG status
    print("\nStep 4: Verifying ingestion...")
    get_rag_status()

    # Step 5: Test query
    print("\nStep 5: Testing chatbot with sample query...")
    test_query()

    print(f"\n{'='*60}")
    print("✅ Knowledge base population completed successfully!")
    print(f"{'='*60}")
    print("\nYou can now use the chatbot with RAG-enhanced responses.")
    print("Try asking questions about:")
    print("  - Oil change services")
    print("  - Brake repair")
    print("  - Business hours")
    print("  - Pricing information")
    print("  - Warranty details")
    print("\nFor more information, see RAG_SETUP_GUIDE.md")


if __name__ == "__main__":
    main()
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from openai import OpenAI
import logging
from django.conf import settings

from .serializers import ChatMessageSerializer, ChatResponseSerializer

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    request_body=ChatMessageSerializer,
    responses={
        200: openapi.Response(
            description='Successful AI chat response',
            schema=ChatResponseSerializer
        ),
        400: openapi.Response(
            description='Bad request - invalid message format',
            schema=ChatResponseSerializer
        ),
        500: openapi.Response(
            description='Internal server error - AI service unavailable',
            schema=ChatResponseSerializer
        ),
    },
    operation_description='Send a message to AI and get a response back using OpenRouter with DeepSeek model',
    operation_summary='AI Chat',
    tags=['Chat'],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    """
    Send a message to AI and get a response back using OpenRouter with DeepSeek model.
    
    This endpoint allows authenticated users to have a conversation with AI.
    The AI acts as a helpful assistant for cinema-related queries.
    """
    serializer = ChatMessageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid message format',
            'response': ''
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user_message = serializer.validated_data['message']
    
    try:
        # Initialize OpenAI client for OpenRouter with explicit parameters
        import httpx
        client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            http_client=httpx.Client(timeout=30.0)
        )
        
        # Create chat completion
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant for Lumo Cinema. You can help users with movie recommendations, cinema information, booking assistance, and general cinema-related questions. Be friendly and informative."
                },
                {
                    "role": "user", 
                    "content": user_message
                },
            ],
            extra_headers={
                "HTTP-Referer": "https://lumo-cinema.com",  # Optional site URL for rankings
                "X-Title": "Lumo Cinema Assistant",  # Optional site title for rankings
            },
            extra_body={},
            stream=False,
            max_tokens=500,
            temperature=0.7,
        )
        
        ai_response = response.choices[0].message.content
        
        logger.info(f"AI chat request from user {request.user.id}: {user_message[:50]}...")
        
        return Response({
            'success': True,
            'response': ai_response,
            'error': ''
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"OpenRouter API error: {str(e)}")
        
        return Response({
            'success': False,
            'error': 'AI service temporarily unavailable. Please try again later.',
            'response': ''
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
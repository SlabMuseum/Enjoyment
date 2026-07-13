Shader "Custom/URPTransparentFadeSpecular"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (1,1,1,1)
        _BaseMap ("Base Map", 2D) = "white" {}
        _Smoothness ("Smoothness", Range(0.0, 1.0)) = 0.5
        _Metallic ("Metallic", Range(0.0, 1.0)) = 0.0
    }
    SubShader
    {
        Tags {"Queue"="Transparent" "RenderType"="Transparent"}
        LOD 200

        Pass
        {
            Tags {"LightMode"="UniversalForward"}

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
            };

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor;
                float _Smoothness;
                float _Metallic;
                TEXTURE2D(_BaseMap);
                SAMPLER(sampler_BaseMap);
            CBUFFER_END

            Varyings vert(Attributes input)
            {
                Varyings output;
                output.positionHCS = TransformObjectToHClip(input.positionOS);
                output.uv = input.uv;
                output.positionWS = TransformObjectToWorld(input.positionOS).xyz;
                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                half4 baseColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;
                half alpha = baseColor.a;

                // Fade out specular and metallic properties with alpha
                half smoothness = _Smoothness * alpha;
                half metallic = _Metallic * alpha;

                // Calculate lighting
                half3 diffuse = baseColor.rgb;
                half3 specular = half3(0, 0, 0);

                // Apply lighting
                Light mainLight = GetMainLight();
                half3 lightDir = normalize(mainLight.direction);
                half3 viewDir = normalize(_WorldSpaceCameraPos - input.positionWS);
                half3 normal = normalize(input.positionWS);
                half3 reflectDir = reflect(-lightDir, normal);

                half3 ambient = UNITY_LIGHTMODEL_AMBIENT.rgb * diffuse;
                half3 diffuseLight = max(dot(normal, lightDir), 0.0) * mainLight.color.rgb * diffuse;
                half3 specularLight = pow(max(dot(viewDir, reflectDir), 0.0), smoothness * 128.0) * mainLight.color.rgb * metallic;

                half3 color = ambient + diffuseLight + specularLight;

                return half4(color, alpha);
            }
            ENDHLSL
        }
    }
    FallBack "Universal Render Pipeline/Lit"
}
